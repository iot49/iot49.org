/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2020  Bernhard Boser
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */


#include <stdio.h>
#include <inttypes.h>

#include "py/obj.h"
#include "py/runtime.h"
#include "py/binary.h"
#include "py/objarray.h"
#include "py/objlist.h"
#include "py/objstringio.h"
#include "py/parsenum.h"
#include "py/stream.h"

#define MP_OBJ_IS_METH(o) (MP_OBJ_IS_OBJ(o) && (((mp_obj_base_t*)MP_OBJ_TO_PTR(o))->type->name == MP_QSTR_bound_method))


//////////////////////////////////////////////////////////////////////////////
// ExtType

typedef struct {
    mp_obj_base_t base;
    int32_t code;
    mp_obj_t data;
} mod_msgpack_extype_obj_t;

const mp_obj_type_t mod_msgpack_exttype_type;

//| class ExtType:
//|     """ExtType represents ext type in msgpack."""
//|     def __init__(self, code: int, data: bytes) -> None:
//|         """Constructor
//|         :param int code: type code in range 0~127.
//|         :param bytes data: representation."""

STATIC mp_obj_t mod_msgpack_exttype_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mod_msgpack_extype_obj_t *self = m_new_obj(mod_msgpack_extype_obj_t);
    self->base.type = &mod_msgpack_exttype_type;

    if (n_args != 2) {
        mp_raise_TypeError(MP_ERROR_TEXT("constructor takes 2 arguments"));
    }
    int code = mp_obj_get_int(args[0]);
    if (code < 0 || code > 127) {
        mp_raise_ValueError(MP_ERROR_TEXT("code outside range 0~127"));
    }
    self->code = code;
    self->data = args[1];
    return MP_OBJ_FROM_PTR(self);
}

STATIC void mod_msgpack_exttype_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    if (dest[0] != MP_OBJ_NULL) {
        // setter not implemented
        return;
    }
    mod_msgpack_extype_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (attr == MP_QSTR_code) {
        dest[0] = MP_OBJ_NEW_SMALL_INT(self->code);
    } else if (attr == MP_QSTR_data) {
        dest[0] = self->data;
    }
}

const mp_obj_type_t mod_msgpack_exttype_type = {
    { &mp_type_type },
    .name = MP_QSTR_ExtType,
    .make_new = mod_msgpack_exttype_make_new,
    .attr = mod_msgpack_exttype_attr,
};

//////////////////////////////////////////////////////////////////////////////
// pack/unpack

void common_hal_msgpack_pack(mp_obj_t obj, mp_obj_t stream_obj, mp_obj_t default_handler);
mp_obj_t common_hal_msgpack_unpack(mp_obj_t stream_obj, mp_obj_t ext_hook, bool use_list);

////////////////////////////////////////////////////////////////
// stream management

typedef struct _msgpack_stream_t {
    mp_obj_t stream_obj;
    mp_uint_t (*read)(mp_obj_t obj, void *buf, mp_uint_t size, int *errcode);
    mp_uint_t (*write)(mp_obj_t obj, const void *buf, mp_uint_t size, int *errcode);
    int errcode;
} msgpack_stream_t;

STATIC msgpack_stream_t get_stream(mp_obj_t stream_obj, int flags) {
    const mp_stream_p_t *stream_p = mp_get_stream_raise(stream_obj, flags);
    msgpack_stream_t s = {stream_obj, stream_p->read, stream_p->write, 0};
    return s;
}

////////////////////////////////////////////////////////////////
// readers

STATIC void read0(msgpack_stream_t *s, void *buf, mp_uint_t size) {
    if (size == 0) return;
    mp_uint_t ret = s->read(s->stream_obj, buf, size, &s->errcode);
    if (s->errcode != 0) {
        mp_raise_OSError(s->errcode);
    }
    if (ret == 0) {
        mp_raise_msg(&mp_type_EOFError, NULL);
    }
    if (ret < size) {
        mp_raise_ValueError(MP_ERROR_TEXT("short read"));
    }
}

STATIC uint8_t read1(msgpack_stream_t *s) {
    uint8_t res = 0;
    read0(s, &res, 1);
    return res;
}

STATIC uint16_t read2(msgpack_stream_t *s) {
    uint16_t res = 0;
    read0(s, &res, 2);
    int n = 1;
    if (*(char *)&n == 1) res = __builtin_bswap16(res);
    return res;
}

STATIC uint32_t read4(msgpack_stream_t *s) {
    uint32_t res = 0;
    read0(s, &res, 4);
    int n = 1;
    if (*(char *)&n == 1) res = __builtin_bswap32(res);
    return res;
}

STATIC size_t read_size(msgpack_stream_t *s, uint8_t len_index) {
    size_t res = 0;
    switch (len_index) {
        case 0:  res = (size_t)read1(s);  break;
        case 1:  res = (size_t)read2(s);  break;
        case 2:  res = (size_t)read4(s);  break;
    }
    return res;
}

////////////////////////////////////////////////////////////////
// writers

STATIC void write0(msgpack_stream_t *s, const void *buf, mp_uint_t size) {
    mp_uint_t ret = s->write(s->stream_obj, buf, size, &s->errcode);
    if (s->errcode != 0) {
        mp_raise_OSError(s->errcode);
    }
    if (ret == 0) {
        mp_raise_msg(&mp_type_EOFError, NULL);
    }
}

STATIC void write1(msgpack_stream_t *s, uint8_t obj) {
    write0(s, &obj, 1);
}

STATIC void write2(msgpack_stream_t *s, uint16_t obj) {
    int n = 1;
    if (*(char *)&n == 1) obj = __builtin_bswap16(obj);
    write0(s, &obj, 2);
}

STATIC void write4(msgpack_stream_t *s, uint32_t obj) {
    int n = 1;
    if (*(char *)&n == 1) obj = __builtin_bswap32(obj);
    write0(s, &obj, 4);
}

// compute and write msgpack size code (array structures)
STATIC void write_size(msgpack_stream_t *s, uint8_t code, size_t size) {
    if ((uint8_t)size == size) {
        write1(s, code);
        write1(s, size);
    } else if ((uint16_t)size == size) {
        write1(s, code+1);
        write2(s, size);
    } else {
        write1(s, code+2);
        write4(s, size);
    }
}

////////////////////////////////////////////////////////////////
// packers

// This is a helper function to iterate through a dictionary.  The state of
// the iteration is held in *cur and should be initialised with zero for the
// first call.  Will return NULL when no more elements are available.
STATIC mp_map_elem_t *dict_iter_next(mp_obj_dict_t *dict, size_t *cur) {
    size_t max = dict->map.alloc;
    mp_map_t *map = &dict->map;

    for (size_t i = *cur; i < max; i++) {
        if (MP_MAP_SLOT_IS_FILLED(map, i)) {
            *cur = i + 1;
            return &(map->table[i]);
        }
    }

    return NULL;
}

STATIC void pack_int(msgpack_stream_t *s, int32_t x) {
    if (x > -32 && x < 128) {
        write1(s, x);
    } else if ((int8_t)x == x) {
        write1(s, 0xd0);
        write1(s, x);
    } else if ((int16_t)x == x) {
        write1(s, 0xd1);
        write2(s, x);
    } else {
        write1(s, 0xd2);
        write4(s, x);
    }
}

STATIC void pack_bin(msgpack_stream_t *s, const uint8_t* data, size_t len) {
    write_size(s, 0xc4, len);
    if (len > 0) write0(s, data, len);
}

STATIC void  pack_ext(msgpack_stream_t *s, int8_t code, const uint8_t* data, size_t len) {
    if (len == 1) {
        write1(s, 0xd4);
    } else if (len == 2) {
        write1(s, 0xd5);
    } else if (len == 4) {
        write1(s, 0xd6);
    } else if (len == 8) {
        write1(s, 0xd7);
    } else if (len == 16) {
        write1(s, 0xd8);
    } else {
        write_size(s, 0xc7, len);
    }
    write1(s, code);    // type byte
    if (len > 0) write0(s, data, len);
}

STATIC void pack_str(msgpack_stream_t *s, const char* str, size_t len) {
    if (len < 32) {
        write1(s, 0b10100000 | (uint8_t)len);
    } else {
        write_size(s, 0xd9, len);
    }
    if (len > 0) write0(s, str, len);
}

STATIC void pack_array(msgpack_stream_t *s, size_t len) {
    // only writes the header, manually write the objects after calling pack_array!
    if (len < 16) {
        write1(s, 0b10010000 | (uint8_t)len);
    } else if (len < 0x10000) {
        write1(s, 0xdc);
        write2(s, len);
    } else {
        write1(s, 0xdd);
        write4(s, len);
    }
}

STATIC void pack_dict(msgpack_stream_t *s, size_t len) {
    // only writes the header, manually write the objects after calling pack_array!
    if (len < 16) {
        write1(s, 0b10000000 | (uint8_t)len);
    } else if (len < 0x10000) {
        write1(s, 0xde);
        write2(s, len);
    } else {
        write1(s, 0xdf);
        write4(s, len);
    }
}

STATIC void pack(mp_obj_t obj, msgpack_stream_t *s, mp_obj_t default_handler) {
    if (MP_OBJ_IS_SMALL_INT(obj)) {
        // int
        int32_t x = MP_OBJ_SMALL_INT_VALUE(obj);
        pack_int(s, x);
    } else if (obj == mp_const_none) {
        write1(s, 0xc0);
    } else if (obj == mp_const_false) {
        write1(s, 0xc2);
    } else if (obj == mp_const_true) {
        write1(s, 0xc3);
    } else if (mp_obj_is_float(obj)) {
        union Float { mp_float_t f;  uint32_t u; };
        union Float data;
        data.f = mp_obj_float_get(obj);
        write1(s, 0xca);
        write4(s, data.u);
    } else if (MP_OBJ_IS_STR(obj)) {
        // string
        size_t len;
        const char *data = mp_obj_str_get_data(obj, &len);
        pack_str(s, data, len);
    } else if (MP_OBJ_IS_TYPE(obj, &mod_msgpack_exttype_type)) {
        mod_msgpack_extype_obj_t *ext = MP_OBJ_TO_PTR(obj);
        mp_buffer_info_t bufinfo;
        mp_get_buffer_raise(ext->data, &bufinfo, MP_BUFFER_READ);
        pack_ext(s, ext->code, bufinfo.buf, bufinfo.len);
    } else if (MP_OBJ_IS_TYPE(obj, &mp_type_tuple)) {
        // tuple
        mp_obj_tuple_t *self = MP_OBJ_TO_PTR(obj);
        pack_array(s, self->len);
        for (size_t i=0;  i<self->len;  i++) {
            pack(self->items[i], s, default_handler);
        }
    } else if (MP_OBJ_IS_TYPE(obj, &mp_type_list)) {
        // list (layout differs from tuple)
        mp_obj_list_t *self = MP_OBJ_TO_PTR(obj);
        pack_array(s, self->len);
        for (size_t i=0;  i<self->len;  i++) {
            pack(self->items[i], s, default_handler);
        }
    } else if (MP_OBJ_IS_TYPE(obj, &mp_type_dict)) {
        // dict
        mp_obj_dict_t *self = MP_OBJ_TO_PTR(obj);
        pack_dict(s, self->map.used);
        size_t cur = 0;
        mp_map_elem_t *next = NULL;
        while ((next = dict_iter_next(self, &cur)) != NULL) {
            pack(next->key, s, default_handler);
            pack(next->value, s, default_handler);
        }
    } else {
        mp_buffer_info_t bufinfo;
        if (mp_get_buffer(obj, &bufinfo, MP_BUFFER_READ)) {
            // bytes (bin type)
            pack_bin(s, bufinfo.buf, bufinfo.len);
        } else if (default_handler != mp_const_none) {
            // set default_handler to mp_const_none to avoid infinite recursion
            // this also precludes some valid outputs
            pack(mp_call_function_1(default_handler, obj), s, mp_const_none);
        } else {
            mp_raise_ValueError(MP_ERROR_TEXT("no default packer"));
        }
    }
}

////////////////////////////////////////////////////////////////
// unpacker

STATIC mp_obj_t unpack(msgpack_stream_t *s, mp_obj_t ext_hook, bool use_list);

STATIC mp_obj_t unpack_array_elements(msgpack_stream_t *s, size_t size, mp_obj_t ext_hook, bool use_list) {
    if (use_list) {
        mp_obj_list_t *t = MP_OBJ_TO_PTR(mp_obj_new_list(size, NULL));
        for (size_t i=0; i<size; i++) {
            t->items[i] = unpack(s, ext_hook, use_list);
        }
        return MP_OBJ_FROM_PTR(t);
    } else {
        mp_obj_tuple_t *t = MP_OBJ_TO_PTR(mp_obj_new_tuple(size, NULL));
        for (size_t i=0; i<size; i++) {
            t->items[i] = unpack(s, ext_hook, use_list);
        }
        return MP_OBJ_FROM_PTR(t);
    }
}

STATIC mp_obj_t unpack_bytes(msgpack_stream_t *s, size_t size) {
    vstr_t vstr;
    vstr_init_len(&vstr, size);
    byte *p = (byte*)vstr.buf;
    // read in chunks: (some drivers - e.g. UART) limit the
    // maximum number of bytes that can be read at once
    // read0(s, p, size);
    while (size > 0) {
        int n = size > 256 ? 256 : size;
        read0(s, p, n);
        size -= n;
        p += n;
    }
    return mp_obj_new_str_from_vstr(&mp_type_bytes, &vstr);
}

STATIC mp_obj_t unpack_ext(msgpack_stream_t *s, size_t size, mp_obj_t ext_hook) {
    int8_t code = read1(s);
    mp_obj_t data = unpack_bytes(s, size);
    if (ext_hook != mp_const_none) {
        return mp_call_function_2(ext_hook, MP_OBJ_NEW_SMALL_INT(code), data);
    } else {
        mod_msgpack_extype_obj_t *o = m_new_obj(mod_msgpack_extype_obj_t);
        o->base.type = &mod_msgpack_exttype_type;
        o->code = code;
        o->data = data;
        return MP_OBJ_FROM_PTR(o);
    }
}

STATIC mp_obj_t unpack(msgpack_stream_t *s, mp_obj_t ext_hook, bool use_list) {
    uint8_t code = read1(s);
    if (((code & 0b10000000) == 0) || ((code & 0b11100000) == 0b11100000)) {
        // int
        return MP_OBJ_NEW_SMALL_INT((int8_t)code);
    }
    if ((code & 0b11100000) == 0b10100000) {
        // str
        size_t len = code & 0b11111;
        // allocate on stack; len < 32
        char str[len];
        read0(s, &str, len);
        return mp_obj_new_str(str, len);
    }
    if ((code & 0b11110000) == 0b10010000) {
        // array (list / tuple)
        return unpack_array_elements(s, code & 0b1111, ext_hook, use_list);
    }
    if ((code & 0b11110000) == 0b10000000) {
        // map (dict)
        size_t len = code & 0b1111;
        mp_obj_dict_t *d = MP_OBJ_TO_PTR(mp_obj_new_dict(len));
        for (size_t i=0; i<len; i++) {
            mp_obj_dict_store(d, unpack(s, ext_hook, use_list), unpack(s, ext_hook, use_list));
        }
        return MP_OBJ_FROM_PTR(d);
    }
    switch (code) {
        case 0xc0: return mp_const_none;
        case 0xc2: return mp_const_false;
        case 0xc3: return mp_const_true;
        case 0xc4:
        case 0xc5:
        case 0xc6: {
            // bin 8, 16, 32
            return unpack_bytes(s, read_size(s, code-0xc4));
        }
        case 0xcc: // uint8
        case 0xd0: // int8
            return MP_OBJ_NEW_SMALL_INT((int8_t)read1(s));
        case 0xcd: // uint16
        case 0xd1: // int16
            return MP_OBJ_NEW_SMALL_INT((int16_t)read2(s));
        case 0xce: // uint32
        case 0xd2: // int32
            return MP_OBJ_NEW_SMALL_INT((int32_t)read4(s));
        case 0xca: {
            union Float { mp_float_t f;  uint32_t u; };
            union Float data;
            data.u = read4(s);
            return mp_obj_new_float(data.f);
        }
        case 0xd9:
        case 0xda:
        case 0xdb: {
            // str 8, 16, 32
            size_t size = read_size(s, code-0xd9);
            vstr_t vstr;
            vstr_init_len(&vstr, size);
            byte *p = (byte*)vstr.buf;
            read0(s, p, size);
            return mp_obj_new_str_from_vstr(&mp_type_str, &vstr);
        }
        case 0xde:
        case 0xdf: {
            // map 16 & 32
            size_t len = read_size(s, code - 0xde + 1);
            mp_obj_dict_t *d = MP_OBJ_TO_PTR(mp_obj_new_dict(len));
            for (size_t i=0; i<len; i++) {
                mp_obj_dict_store(d, unpack(s, ext_hook, use_list), unpack(s, ext_hook, use_list));
            }
            return MP_OBJ_FROM_PTR(d);
        }
        case 0xdc:
        case 0xdd: {
            // array 16 & 32
            size_t size = read_size(s, code - 0xdc + 1);
            return unpack_array_elements(s, size, ext_hook, use_list);
        }
        case 0xd4:      // fixenxt 1
            return unpack_ext(s, 1, ext_hook);
        case 0xd5:      // fixenxt 2
            return unpack_ext(s, 2, ext_hook);
        case 0xd6:      // fixenxt 4
            return unpack_ext(s, 4, ext_hook);
        case 0xd7:      // fixenxt 8
            return unpack_ext(s, 8, ext_hook);
        case 0xd8:      // fixenxt 16
            return unpack_ext(s, 16, ext_hook);
        case 0xc7:      // ext 8
        case 0xc8:      // ext 16
        case 0xc9:
            // ext 8, 16, 32
            return unpack_ext(s, read_size(s, code-0xc7), ext_hook);
        case 0xc1:      // never used
        case 0xcb:      // float 64
        case 0xcf:      // uint 64
        case 0xd3:      // int 64
        default:
            mp_raise_NotImplementedError(MP_ERROR_TEXT("64 bit types"));
    }
}

void common_hal_msgpack_pack(mp_obj_t obj, mp_obj_t stream_obj, mp_obj_t default_handler) {
    msgpack_stream_t stream = get_stream(stream_obj, MP_STREAM_OP_WRITE);
    pack(obj, &stream, default_handler);
}

mp_obj_t common_hal_msgpack_unpack(mp_obj_t stream_obj, mp_obj_t ext_hook, bool use_list) {
    msgpack_stream_t stream = get_stream(stream_obj, MP_STREAM_OP_WRITE);
    return unpack(&stream, ext_hook, use_list);
}


//| """Pack object in msgpack format
//|
//| The msgpack format is similar to json, except that the encoded data is binary.
//| See https://msgpack.org for details. The module implements a subset of the cpython
//| module msgpack-python.
//|
//| Not implemented: 64-bit int, uint, float.
//|
//| Example 1:
//|    import msgpack
//|    from io import BytesIO
//|
//|    b = BytesIO()
//|    msgpack.pack({'list': [True, False, None, 1, 'abc'], 'str': 'blah'}, b)
//|    b.seek(0)
//|    print(msgpack.unpack(b))
//|
//| Example 2: handling objects
//|
//|    from msgpack import pack, unpack, ExtType
//|    from io import BytesIO
//|
//|    class MyClass:
//|        def __init__(self, val):
//|            self.value = val
//|        def __str__(self):
//|            return str(self.value)
//|
//|    data = MyClass(b'my_value')
//|
//|    def encoder(obj):
//|        if isinstance(obj, MyClass):
//|            return ExtType(1, obj.value)
//|        return f"no encoder for {obj}"
//|
//|    def decoder(code, data):
//|        if code == 1:
//|            return MyClass(data)
//|        return f"no decoder for type {code}"
//|
//|    buffer = BytesIO()
//|    pack(data, buffer, default=encoder)
//|    buffer.seek(0)
//|    decoded = unpack(buffer, ext_hook=decoder)
//|    print(f"{data} -> {buffer.getvalue()} -> {decoded}")
//| """


//| def pack(obj: object, buffer: WriteableBuffer, *, default: Function=None) -> None:
//|     """Ouput object to buffer in msgpack format.
//|     :param object obj: Object to convert to msgpack format.
//|     :param ~_typing.WriteableBuffer buffer: buffer to write into
//|     :param Optional[~_typing.Callable[[object], None]] default:
//|           function called for python objects that do not have
//|           a representation in msgpack format.
//|     """

STATIC mp_obj_t mod_msgpack_pack(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_obj, ARG_buffer, ARG_default };
    STATIC const mp_arg_t allowed_args[] = {
        { MP_QSTR_obj, MP_ARG_REQUIRED | MP_ARG_OBJ, { .u_obj = mp_const_none } },
        { MP_QSTR_buffer, MP_ARG_REQUIRED | MP_ARG_OBJ, { .u_obj = mp_const_none } },
        { MP_QSTR_default, MP_ARG_KW_ONLY | MP_ARG_OBJ, { .u_obj = mp_const_none } },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_obj_t handler = args[ARG_default].u_obj;
    if (handler != mp_const_none && !MP_OBJ_IS_FUN(handler) && !MP_OBJ_IS_METH(handler)) {
        mp_raise_ValueError(MP_ERROR_TEXT("default is not a function"));
    }

    common_hal_msgpack_pack(args[ARG_obj].u_obj, args[ARG_buffer].u_obj, handler);
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_KW(mod_msgpack_pack_obj, 1, mod_msgpack_pack);

//| def unpack(buffer: ReadableBuffer, *, ext_hook: Function=None, use_list: bool=True) -> object:
//|     """Unpack and return one object from buffer.
//|     :param ~_typing.ReadableBuffer buffer: buffer to read from
//|     :param Optional[~_typing.Callable[[int, bytes], object]] ext_hook: function called for objects in
//|            msgpack ext format.
//|     :param Optional[bool] use_list: return array as list or tuple (use_list=False).
//|     :return object: object read from buffer.
//|     """

STATIC mp_obj_t mod_msgpack_unpack(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum { ARG_buffer, ARG_ext_hook, ARG_use_list };
    STATIC const mp_arg_t allowed_args[] = {
        { MP_QSTR_buffer, MP_ARG_REQUIRED | MP_ARG_OBJ, { .u_obj = mp_const_none }, },
        { MP_QSTR_ext_hook, MP_ARG_KW_ONLY | MP_ARG_OBJ, { .u_obj = mp_const_none } },
        { MP_QSTR_use_list, MP_ARG_KW_ONLY | MP_ARG_BOOL, { .u_bool = true } },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_obj_t hook = args[ARG_ext_hook].u_obj;
    if (hook != mp_const_none && !MP_OBJ_IS_FUN(hook) && !MP_OBJ_IS_METH(hook)) {
        mp_raise_ValueError(MP_ERROR_TEXT("ext_hook is not a function"));
    }

    return common_hal_msgpack_unpack(args[ARG_buffer].u_obj, hook, args[ARG_use_list].u_bool);
}
MP_DEFINE_CONST_FUN_OBJ_KW(mod_msgpack_unpack_obj, 1, mod_msgpack_unpack);


STATIC const mp_rom_map_elem_t msgpack_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_umsgpack) },
    { MP_ROM_QSTR(MP_QSTR_ExtType), MP_ROM_PTR(&mod_msgpack_exttype_type) },
    { MP_ROM_QSTR(MP_QSTR_pack), MP_ROM_PTR(&mod_msgpack_pack_obj) },
    { MP_ROM_QSTR(MP_QSTR_unpack), MP_ROM_PTR(&mod_msgpack_unpack_obj) },
};

STATIC MP_DEFINE_CONST_DICT(msgpack_module_globals, msgpack_module_globals_table);

const mp_obj_module_t mp_module_umsgpack = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&msgpack_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_msgpack, mp_module_umsgpack, 1);
