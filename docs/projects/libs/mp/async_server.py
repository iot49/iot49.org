import uasyncio as asyncio
import os, io, sys, socket, struct, msgpack, secrets, time

try:
    from iot import dupterm
except ImportError:
    from uos import dupterm

VERSION = 'ns-V1'
EOT     = b'\x04'

class Bye(Exception):
    pass

class Server(io.IOBase):

    def __init__(self, port=1234):
        self.buffer = bytearray(2048)
        self.globals = globals()

    async def serve(self, rw, _):
        self._rw = rw
        print("serve", rw.get_extra_info("peername"))
        try:
            # send version
            self.write(VERSION)
            self.write(b'\n')
            # check password
            pwd = await self.readline()
            if pwd != getattr(secrets, 'mp_pwd', ''):
                rw.write(b'wrong password\n')
                await rw.drain()
                return
            self.write(b'OK\n')
            while True:
                try:
                    # read request header
                    req = await self.readline()
                    if req == '':
                        # client hung up
                        return
                    # handle request
                    await getattr(self, 'do_' + req)()
                except Bye:
                    return
                except Exception as e:
                    print("Exception in serve:", e)
                    sys.print_exception(e)
                    # Close connection (safe way to purge data in the pipe?)
                    return
        finally:
            await rw.wait_closed()


    async def do_bye(self):
        # end current session
        raise Bye

    async def do_evex(self):
        # client: send code length in bytes
        # client: send code
        # server: send OK
        # server: send resonse EOT error EOT
        length = int(await self.readline())
        if length > len(self.buffer):
            mv = memoryview(bytearray(length))
        else:
            mv = memoryview(self.buffer)[0:length]
        n = 0
        while n < length:
            await self._rw.read(0)
            n += self._rw.s.readinto(mv[n:min(n+256, length)])
        self.write(b'OK\n')
        # workaround for bug in iot.dupterm
        try:
            import machine
            dterm = dupterm(self)
        except:
            dterm = dupterm()
            dupterm(self)
        try:
            exec(mv, self.globals)
            self.write(EOT)
        except Exception as e:
            self.write(EOT)
            sys.print_exception(e)
        finally:
            dupterm(dterm)
        self.write(EOT)

    async def do_fput(self):
        # client: send path
        # client: send file size
        # client: send file content
        # server: send OK or error
        path = await self.readline()
        size = int(await self.readline())
        rw = self._rw
        mv = memoryview(self.buffer)
        try:
            with open(path, 'wb') as f:
                while size > 0:
                    n = rw.s.readinto(mv[:min(size, len(self.buffer))])
                    f.write(mv[:n])
                    size -= n
                    time.sleep(0.1)
            rw.write(b'OK\n')
            await rw.drain()
        except Exception as e:
            print("*** fput", e)
            rw.write(str(e).encode())
            rw.write(b'\n')
            await rw.drain()
            raise

    async def do_fget(self):
        # client: send path
        # server: send OK or error
        # server: send file size
        # server: send file contents
        path = await self.readline()
        rw = self._rw
        try:
            # error if file doesn't exist ...
            size = os.stat(path)[6]
            rw.write(b'OK\n')
            await rw.drain()
        except Exception as e:
            print("*** fget", e)
            rw.write(str(e).encode())
            rw.write(b'\n')
            await rw.drain()
            return
        rw.write(str(size))
        rw.write(b'\n')
        await rw.drain()
        mv = memoryview(self.buffer)
        # what if file does not exist?
        with open(path, 'rb') as f:
            while size > 0:
                n = f.readinto(mv[:min(size, len(self.buffer))])
                await asyncio.sleep_ms(0)
                rw.s.write(mv[:n])
                size -= n

    async def do_echo(self):
        # client: send length
        # client: send data
        # server: send data (back), simultaneous with receiving it
        rw = self._rw
        length = int(await self.readline())
        sz = len(self.buffer)
        mv = memoryview(self.buffer)
        while length > 0:
            await rw.read(0)
            n = rw.s.readinto(mv[0:min(length,sz)])
            rw.write(mv[0:n])
            length -= n

    async def readline(self):
        l = await self._rw.readline()
        return l[:-1].decode()

    # dupterm
    def write(self, data):
        try:
            self._rw.s.write(data)
        except Exception:
            # ECONNRESET, should not happen
            pass

    def readinto(self, b):
        return None


async def start_async_server(port=54321):
    import network

    ip = network.WLAN(network.STA_IF).ifconfig()[0]
    print("mp://{}:{}".format(ip, port))
    # advertise
    network.WLAN(network.STA_IF).mdns_add_service('_mp', '_tcp', port)
    # serve
    s = Server()
    await asyncio.start_server(s.serve, ip, port, 1)
