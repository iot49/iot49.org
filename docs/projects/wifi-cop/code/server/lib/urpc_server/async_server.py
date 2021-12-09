import uasyncio as asyncio
import msgpack, io, os, sys

# object registry
# concrete objects on server are represented by _Proxy on client
_registry = {}         # int --> object
_registry_n = 0        # next registered object number

class Duptermer(io.IOBase):
    def write(self, data):
        global _stream
        msgpack.pack(msgpack.ExtType(3, data), _stream)
    def readinto(self, b):
        return None


def ver(_):
    """Protocol version"""
    return 'V1'

def re(_):
    """Registry (for debugging)"""
    res = {}
    for k,v in _registry.items():
        res[int.from_bytes(k, 'big')] = repr(v)
    return res

def im(args):
    """Import module"""
    exec("import {}".format(args[0]))
    return locals()[args[0]]

def ex(args):
    """Execute on server"""
    dterm = os.dupterm(Duptermer())
    try:
        exec(args[0], globals())
    finally:
        os.dupterm(dterm)

def cm(args):
    """Call instance method"""
    dterm = os.dupterm(Duptermer())
    try:
        return getattr(args[0], args[1])(*args[2], **args[3])
    finally:
        os.dupterm(dterm)

def gp(args):
    """Get property"""
    return getattr(args[0], args[1])

def sp(args):
    """Set property"""
    return setattr(args[0], args[1], args[2])

def ri(args):
    """obj.readinto(buffer)"""
    global _stream
    sz = args[1]
    if sz > len(_buffer): sz = len(_buffer)
    mv = memoryview(_buffer[:sz])
    # read & update sz to actual number of bytes read
    sz = args[0].readinto(mv)
    # send actual number of bytes read
    msgpack.pack(sz, _stream)
    # send raw bytes (easier to decode by client)
    _stream.write(mv[:sz])
    # result sent aleady
    return None

def _d(args):
    """Remove object from registry, __del__"""
    try:
        del _registry[args[0]]
    except KeyError:
        # deleted already
        pass

def _s(args):
    """__str__"""
    return str(args[0])

def eq(args):
    """Equality"""
    return args[0] == args[1]

def _id(args):
    """Object id"""
    return id(args[0])

def _ext_handler(code, data):
    # convert ExtType to object
    assert code == 1
    return _registry.get(data)

def _obj_handler(obj):
    # convert object to ExtType
    global _registry_n
    _registry_n += 1
    obj_id = _registry_n.to_bytes(4, 'big')
    _registry[obj_id] = obj
    return msgpack.ExtType(1, obj_id)


async def async_serve(uart, buffer_size=256):
    """Start urcp server"""
    global _stream, _buffer
    _stream = uart
    a_stream = asyncio.StreamReader(uart)
    _buffer = bytearray(buffer_size)
    print("serve ...")
    while True:
        # wait for request
        await a_stream.read(0)
        try:
            req = msgpack.unpack(uart, ext_hook=_ext_handler, use_list=False)
            result = globals().get(req[0])(req[1:])
        except Exception as e:
            print("Exception", e)
            sys.print_exception(e, uart)
            data = "{}\x04{}\x04{}".format(e.__class__.__name__, e.args, s.getvalue())
            result = msgpack.ExtType(2, data.encode())
        msgpack.pack(result, uart, default=_obj_handler)
