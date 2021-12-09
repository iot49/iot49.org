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
        self.buffer = bytearray(512)
        self.globals = globals()
        self.dterm = None
        self.ss = ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ss.setblocking(False)

        ai = socket.getaddrinfo('', port)
        addr = ai[0][4]
        ss.bind(addr)
        ss.listen(1)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.ss.close()

    def readline(self):
        return self._sock.readline().strip().decode()

    def accept(self):
        """Accept connection and serve request.
        Returns immadiately if no client is waiting."""
        try:
            cs, addr = self.ss.accept()
        except Exception as e:
            return
        # cs.setblocking(True)
        cs.settimeout(5000)
        self._sock = cs
        print("accepted connection from", addr)
        try:
            cs.write(VERSION)
            cs.write(b'\n')
            pwd = self.readline()
            if pwd != getattr(secrets, 'mp_pwd', ''):
                cs.write(b'wrong password\n')
                return
            cs.write(b'OK\n')
            self.serve()
        except Exception as e:
            print("*** accept", e)
        finally:
            cs.close()
            print("\nclosed client connection")

    def serve(self):
        # multiple requests or just one?
        while True:
            try:
                # read request header
                req = self.readline()
                if len(req) == 0: continue
                # handle request
                getattr(self, 'do_' + req)()
            except Bye:
                return
            except Exception as e:
                print("Exception in serve:", e)
                sys.print_exception(e)
                # Close connection (safe way to purge data in the pipe?)
                return

    def do_bye(self):
        # end current session
        raise Bye

    def do_evex(self):
        # client: send code length in bytes
        # client: send code
        # server: send OK
        # server: send resonse EOT error EOT
        length = int(self.readline())
        if length > len(self.buffer):
            mv = memoryview(bytearray(length))
        else:
            mv = memoryview(self.buffer)[0:length]
        n = 0
        while n < length:
            n += self._sock.readinto(mv[n:min(n+256, length)])
        self.write(b'OK\n')
        # workaround for bug in iot.dupterm
        # dterm = dupterm(self)
        dterm = dupterm()
        dupterm(self)
        try:
            exec(mv, self.globals)
            self._sock.write(EOT)
        except Exception as e:
            self._sock.write(EOT)
            sys.print_exception(e)
        finally:
            dupterm(dterm)
        self._sock.write(EOT)

    def do_fput(self):
        # client: send path
        # client: send file size
        # client: send file content
        # server: send OK or error
        path = self.readline()
        size = int(self.readline())
        sock = self._sock
        mv = memoryview(self.buffer)
        try:
            with open(path, 'wb') as f:
                while size > 0:
                    n = sock.readinto(mv[:min(size, len(self.buffer))])
                    f.write(mv[:n])
                    size -= n
                    time.sleep(0.1)
                    if False:
                        data = sock.read(min(size, 512))
                        f.write(data)
                        size -= len(data)
            sock.write(b'OK\n')
        except Exception as e:
            print("*** fput", e)
            sock.write(str(e).encode())
            sock.write(b'\n')
            raise

    def do_fget(self):
        # client: send path
        # server: send OK or error
        # server: send file size
        # server: send file contents
        path = self.readline()
        sock = self._sock
        try:
            size = os.stat(path)[6]
            sock.write(b'OK\n')
        except Exception as e:
            print("*** fget", e)
            sock.write(str(e).encode())
            sock.write(b'\n')
            return
        sock.write(str(size))
        sock.write(b'\n')
        mv = memoryview(self.buffer)
        # what if file does not exist?
        with open(path, 'rb') as f:
            while size > 0:
                n = f.readinto(mv[:min(size, len(self.buffer))])
                sock.write(mv[:n])
                size -= n

    def do_echo(self):
        # client: send length
        # client: send data
        # server: send data (back), simultaneous with receiving it
        length = int(self.readline())
        sz = len(self.buffer)
        mv = memoryview(self.buffer)
        while length > 0:
            n = self._sock.readinto(mv[0:min(length,sz)])
            self._sock.write(mv[0:n])
            length -= n

    # dupterm
    def write(self, data):
        try:
            self._sock.write(data)
        except Exception:
            # ECONNRESET, should not happen
            pass
            dupterm(None)
            print("*** dupterm write ECONNRESET")

    def readinto(self, b):
        return None


def start_server(port=54321):
    with Server(port) as server:

        # advertise
        import network, time
        network.WLAN(network.STA_IF).mdns_add_service('_mp', '_tcp', port)

        ip = network.WLAN(network.STA_IF).ifconfig()[0]
        print("mp://{}:{}".format(ip, port))

        try:
            print("accept ...")
            while True:
                server.accept()
                time.sleep(0.2)
        except Exception as e:
            print("so long", e)

# start_server()
