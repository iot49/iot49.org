/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2021  Bernhard Boser
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

 /*
 Attempt to make sockets (and perhaps other streams) available over RPC to a poller on the client.
 The client implements a proxy socket object that forwards all operations (recv, send, ...) to
 the actual socket object on the server. 
 This works except for ioctl, which is not available in Python. This class provides this 
 access, but calling it with a socket gives an error:

    from socket import socket
    from ioctl import ioctl

    s = socket()
    print("ioctl s", ioctl(s, 5, 0))

    ***** OSError: [Errno 22] EINVAL
 */

#include "py/runtime.h"
#include "py/obj.h"
#include "py/stream.h"

// mp_uint_t (*ioctl)(mp_obj_t obj, mp_uint_t request, uintptr_t flags, int *errcode);

// Call ioctl on stream object
STATIC mp_obj_t ioctl(mp_obj_t stream_obj, mp_obj_t request_obj, mp_obj_t flags_obj) {
    const mp_stream_p_t *stream_p = mp_get_stream_raise(stream_obj, MP_STREAM_OP_IOCTL);
    mp_uint_t request = mp_obj_get_int(request_obj);
    mp_uint_t flags = mp_obj_get_int(flags_obj);
    int errcode;
    mp_int_t ret = stream_p->ioctl(stream_obj, request, flags, &errcode);
    if (ret == -1) mp_raise_OSError(errcode);
    return mp_obj_new_int(ret);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_3(ioctl_obj, ioctl);

STATIC const mp_rom_map_elem_t ioctl_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_ioctl) },
    { MP_ROM_QSTR(MP_QSTR_ioctl), MP_ROM_PTR(&ioctl_obj) },
};
STATIC MP_DEFINE_CONST_DICT(ioctl_module_globals, ioctl_module_globals_table);

const mp_obj_module_t ioctl_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&ioctl_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_ioctl, ioctl_module, 1);
