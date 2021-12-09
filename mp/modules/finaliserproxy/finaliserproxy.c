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

#include "py/obj.h"
#include "py/runtime.h"

#define MP_OBJ_IS_METH(o) (MP_OBJ_IS_OBJ(o) && (((mp_obj_base_t*)MP_OBJ_TO_PTR(o))->type->name == MP_QSTR_bound_method))


typedef struct {
    mp_obj_base_t base;
    mp_obj_t callback;
} finaliser_proxy_obj_t;

extern const mp_obj_type_t finaliser_proxy_type;


STATIC mp_obj_t finaliser_proxy_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 1, 1, false);

    if (!MP_OBJ_IS_FUN(args[0]) && !MP_OBJ_IS_METH(args[0])) {
        mp_raise_ValueError(MP_ERROR_TEXT("function expected"));
    }

    finaliser_proxy_obj_t *self = m_new_obj_with_finaliser(finaliser_proxy_obj_t);
    self->base.type = &finaliser_proxy_type;
    self->callback = args[0];

    return MP_OBJ_FROM_PTR(self);
}


STATIC mp_obj_t finaliser_proxy_cleanup(mp_obj_t self_in) {
    finaliser_proxy_obj_t *self = MP_OBJ_TO_PTR(self_in);
    // note: self does not point to derived class, hence we supply arg instead
    mp_call_function_0(self->callback);
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(finaliser_proxy_cleanup_obj, finaliser_proxy_cleanup);


STATIC const mp_rom_map_elem_t finaliser_proxy_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR___del__), MP_ROM_PTR(&finaliser_proxy_cleanup_obj) },
};
STATIC MP_DEFINE_CONST_DICT(finaliser_proxy_locals_dict, finaliser_proxy_locals_dict_table);


const mp_obj_type_t finaliser_proxy_type = {
    { &mp_type_type },
    .name = MP_QSTR_FinaliserProxy,
    .make_new = finaliser_proxy_make_new,
    .locals_dict = (mp_obj_dict_t*)&finaliser_proxy_locals_dict,
};


STATIC const mp_rom_map_elem_t finaliser_proxy_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR_FinaliserProxy), MP_ROM_PTR(&finaliser_proxy_type) },
};

STATIC MP_DEFINE_CONST_DICT(module_finaliser_proxy_globals, finaliser_proxy_module_globals_table);

const mp_obj_module_t mp_module_finaliser_proxy = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&module_finaliser_proxy_globals,
};

MP_REGISTER_MODULE(MP_QSTR_finaliserproxy, mp_module_finaliser_proxy, 1);
