import msgpack, struct, time

try:
    from iot import FinaliserProxy
except ImportError:
    try:
        from finaliser_proxy import FinaliserProxy
    except ImportError:
        class FinaliserProxy:
            def __init__(self, arg):
                pass

class RPCError(Exception):
    pass

class _ResultError(Exception):
    # thrown if _ext_handler does not return a result
    pass


_stream = None

def _init():
    from init_urpc_client import get_uart
    global _stream
    _stream = get_uart()
    # CircuitPython/MicroPython API difference
    global _any
    if hasattr(_stream, 'in_waiting'):
        def _any():
            return _stream.in_waiting
    else:
        def _any():
            return _stream.any()

def version_():
    # version check
    ver = _send(("ver", ))
    assert ver == 'V1', "version mismatch, server: {} vs host: V1".format(ver)
    return ver

def registry_():
    # remote object registry
    return _send(("re", ))

def import_(module: str):
    # import module on remote and return a reference
    return _send(("im", module))

def exec_(code: str):
    # execute on server
    return _send(("ex", code))

def eq_(a, b):
    # equality: a == b
    return _send(("eq", a, b))

def id_(obj):
    # object id
    return _send(("_id", obj))

def _obj_handler(obj):
    # convert _Proxy to its ext_type (in _send)
    if isinstance(obj, _Proxy):
        return obj._ext_type
    # should never happen
    raise ValueError("no handler for {}".format(obj))

def _ext_handler(code, data):
    # convert ExtType to _Proxy, etc
    global _stream
    if code == 1:
        return _Proxy(msgpack.ExtType(code, data))
    if code == 2:
        # exception
        # try to re-raise with correct type
        exc, args, tb = data.decode().split('\x04')
        if False:
            print("raise _ext_handler", code, data)
            print("exc ", exc)
            print("args", args)
            print("tb  ", tb)
        # add traceback as last arg
        args = args[:-1]
        if not args.endswith(','): args += ','
        args = "{}{})".format(args, repr(tb))
        # raise the exception
        exec("raise {}{}".format(exc, args))
    if code == 3:
        # print
        print(data.decode(), end="")
        raise _ResultError()
    raise ValueError("uRPC: unknown ExtType({}, {})".format(code, data))

def _clear_rx_buffer():
    global _stream
    while _any():
        print("clear rx buffer:", msgpack.unpack(_stream, ext_hook=_ext_handler, use_list=False))

def _ready_to_read():
    global _stream
    while _any() == 0:
        pass
    
def default_handler(obj):
    if isinstance(obj, _Proxy):
        return obj.ext_type
    raise AttributeError("Cannot send a", type(obj))

def _send(req):
    global _stream
    _clear_rx_buffer()
    try:
        # print("_send", req)
        msgpack.pack(req, _stream, default=default_handler)
    except ValueError as e:
        print("***", e)
        raise
    while True:
        _ready_to_read()
        try:
            return msgpack.unpack(_stream, ext_hook=_ext_handler, use_list=False)
        except _ResultError:
            pass


class _Proxy(FinaliserProxy):

    def __init__(self, ext_type: msgpack.ExtType):
        # _Proxy is a reference (msgpack.ExtType) to an object on the remote
        assert isinstance(ext_type, msgpack.ExtType)
        self._ext_type = ext_type
        super().__init__(self.__del__)

    @property
    def ext_type(self):
        return self._ext_type

    def __getattr__(self, name: str):
        # Note:
        # We return an accessor function rather than a reference to the
        # actual object (method, property) on the server.
        # This avoids an extra rpc call but has the disadvantage that
        # properties cannot accessed the standard way.
        # (_Proxy.x just returns the accessor method, not the property value).
        def method(*args, **kwargs):
            return _send(("cm", self._ext_type, name, args, kwargs))
        return method

    def get_(self, name: str):
        # get object property
        return _send(("gp", self._ext_type, name))

    def set_(self, name: str, value):
        # set object property
        return _send(("sp", self._ext_type, name, value))

    def readinto(self, buffer):
        global _stream
        _clear_rx_buffer()
        msgpack.pack(("ri", self._ext_type, len(buffer)), _stream)
        _ready_to_read()
        # get actual number of bytes read OR handle error (if any)
        sz = msgpack.unpack(_stream, ext_hook=_ext_handler, use_list=False)
        # read data; not all versions of readinto support length argument
        mv = memoryview(buffer)
        # print("urpc client.readinto [sz]")
        _stream.readinto(mv[:sz])
        # server sends an extra None
        assert msgpack.unpack(_stream) == None, "readinto expects terminating 'None'"
        return sz

    # preallocate (heap locked in __del__)
    DEL = [ "_d", None ]

    def __del__(self):
        # reclaim object on remote
        global _stream
        _Proxy.DEL[1] = self._ext_type.data
        msgpack.pack(self.DEL, _stream)
        return msgpack.unpack(_stream)  # read response (None)

    def __str__(self):
        return _send(("_s", self._ext_type))
    
    def __eq__(self, other):
        return id_(self) == id_(other)

_init()

try:
    # check version compatiblity
    version_()
except:
    # the first try often raises EAGAIN on server, just try again
    version_()
