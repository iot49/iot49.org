import os, time
import busio, board
from digitalio import DigitalInOut, DriveMode

EOT = b'\x04'


class ReplError(Exception):
    """Error related to esp32."""
    pass


class ReplClient:

    def __init__(self):
        """ESP32 repl on Particle Argon.
        This code runs on the nrf52 and accesses the esp32 repl.
        """
        self._uploaded_file_ops = False

    def exec(self, code, timeout=10):
        """Send code for evaluation and print result on console."""
        self.__exec_part_1(code)
        ret, ret_err = self.__exec_part_2(timeout)
        if ret_err:
            raise ReplError(ret_err)
        return ret

    def exec_no_output(self, code):
        """Like exec, but returns immediately,
        without waiting for result or error."""
        self.__exec_part_1(code)

    def enable(self, state=True):
        """Power down ESP32 by holding reset low."""
        self.reset_pin = state

    def softreset(self):
        """Reset VM, clearing memory and releasing resources (e.g. gpio)."""
        try:
            self.device.write(b'\x03')   # abort
            self.device.write(b'\x04')   # reset
            self.device.write(b'\r')
            self.__read_until(b'raw REPL; CTRL-B to exit\r\n>')
        except Exception as e:
            raise ReplError(e)

    def hardreset(self, no_sleep=False):
        """Reset ESP32 by asserting reset pin low."""
        self.reset_pin.value = False
        time.sleep(0.2)
        self.reset_pin.value = True
        # wait for MicroPyton prompt
        if not no_sleep:
            self.__read_until(b'information.\r\n>>>', timeout=10)

    def show_boot_messages(self, timeout=5):
        """Hard reset ESP32, then print boot messages."""
        self.hardreset(no_sleep=True)
        self.listen(timeout)

    def listen(self, timeout=2):
        """Print whatever is coming from the ESP32 console"""
        start = time.monotonic()
        while (time.monotonic()-start) < timeout:
            n = self.device.in_waiting
            if n:
                print(self.device.read(n).decode(), end="")
                start = time.monotonic()
            time.sleep(0.001)

    def __flush_input(self):
        """Clear self.device input buffer."""
        self.device.reset_input_buffer()

    def __read_until(self, pattern, timeout=1):
        result = bytearray()
        start = time.monotonic()
        while not result.decode().endswith(pattern):
            if (time.monotonic() - start) > timeout:
                try:
                    result = result.decode()
                    pattern = pattern.decode()
                except:
                    pass
                raise ReplError("Timeout reading from MCU,\n "
                                "got    '{}',\n  expect '{}'".format(result, pattern))
            b = self.device.read(1)
            try:
                result.extend(b)
            except UnicodeError as e:
                print("***** {} in {}.extend({})".format(e, result, repr(b)))
        return result

    def __exec_part_1(self, code):
        if isinstance(code, str):
            code = code.encode()

        # ctrl-C twice: interrupt any running program
        self.device.write(b"\r\x03\x03")
        self.__flush_input()

        # enter raw repl
        self.device.write(b"\r")
        self.device.write(b"\x01")

        # time.sleep(0.1)
        # print(self.device.read(self.device.in_waiting))
        self.__read_until(b'raw REPL; CTRL-B to exit\r\n>')

        # send code & start evaluation
        for i in range(0, len(code), 256):
            self.device.write(code[i : min(i + 256, len(code))])
            time.sleep(0.01)
        self.device.write(EOT)

        # process result, format "OK _answer_ EOT _error_message_ EOT>"
        res = self.device.read(2)
        if res != b'OK':
            rem = self.device.read(self.device.in_waiting)
            raise ReplError("Expected OK, got {}".format(res+rem))

    def __exec_part_2(self, timeout):
        res = self.__read_until(b'\x04', timeout=timeout)
        if res[-1] != 4:
            raise ReplError("timeout waiting for first EOF")
        res = res[:-1]
        err = self.__read_until(b'\x04', timeout=timeout)
        if err[-1] != 4:
            raise ReplError("timeout waiting for second EOF")
        err = err[:-1]

        return res, err.decode()

    # file operations:
    # adapted from https://github.com/micropython/micropython/blob/master/tools/pyboard.py

    def fs_cat(self, src, chunk_size=256):
        cmd = (
            "with open('{}') as _f:\n while 1:\n"
            "  _b=_f.read({})\n  if not _b:break\n  print(_b,end='')".format(src, chunk_size)
        )
        print(self.exec(cmd).decode())

    def fs_get(self, src, dst=None, chunk_size=256):
        if dst == None: dst = src
        self.exec("_f=open('{}','rb')\n_r=_f.read".format(src))
        with open(dst, "wb") as f:
            while True:
                data = self.exec("print(_r({}), end='')".format(chunk_size))
                data = eval(data.decode())
                if not len(data): break
                f.write(data)
        self.exec("_f.close()")

    def fs_put(self, src, dst=None, chunk_size=256):
        if dst == None: dst = src
        self.exec("_f=open('{}','wb')\n_w=_f.write".format(dst))
        with open(src, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data: break
                self.exec("_w(" + repr(data) + ")")
        self.exec("_f.close()")

    def fs_ls(self, dir='/'):
        self.upload_fileops()
        print(self.exec("rlist('{}')".format(dir)).decode())

    def fs_mkdirs(self, dir):
        self.upload_fileops()
        self.exec("makedirs('{}')".format(dir))

    def fs_rm_rf(self, dir):
        self.upload_fileops()
        self.exec("rm_rf('{}')".format(dir))

    def fs_rcopy(self, src, dst=None, level=0):
        if src.startswith('.') or src.startswith('/.'):
            return
        if dst == None: dst = src
        stat = os.stat(src)
        fsize = stat[6]
        mtime = stat[7]
        if stat[0] & 0x4000:
            print("os.mkdir('{}')".format(dst))
            self.fs_mkdirs(dst)
            d = os.listdir(src)
            for p in sorted(d):
                self.fs_rcopy(src + '/' + p, dst + '/' + p, level+1)
        else:
            print("cp {} {}".format(src, dst))
            self.fs_put(src, dst)

    def upload_fileops(self):
        if not self._uploaded_file_ops:
            self.exec(_remote_functions)
            self._uploaded_file_ops = True

    def __enter__(self):
        self.device = busio.UART(tx=board.ESP_RX, rx=board.ESP_TX, \
                            baudrate=115200, timeout=1,
                            receiver_buffer_size=1024)
        reset = DigitalInOut(board.ESP_WIFI_EN)
        reset.switch_to_output(value=True, drive_mode=DriveMode.OPEN_DRAIN)
        self.reset_pin = reset

        return self

    def __exit__(self, *args):
        try:
            self.device.deinit()
        except:
            pass
        try:
            self.reset_pin.deinit()
        except:
            pass
        self.device = None
        self.reset_pin = None


_remote_functions = """
import os

def makedirs(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.args[0] == 2:
            # no such file or directory, create parent first
            makedirs(path[:path.rfind('/')])
            os.mkdir(path)
        elif e.args[0] == 17:
            pass
        else:
            raise

def rm_rf(path):
    try:
        mode = os.stat(path)[0]
        if mode & 0x4000 != 0:
            for file in os.listdir(path):
                rm_rf(path + '/' + file)
            os.rmdir(path)
        else:
            os.remove(path)
    except OSError as e:
        if e.args[0] == 2:
            pass
        else:
            print("--------- OSError", e, e.args[0])

def rlist(path, level=0):
    for _f in os.ilistdir(path):
        print('{}{:12} {}{}'.format(' '*8*level, _f[3]if len(_f)>3 else 0,_f[0],'/'if _f[1]&0x4000 else ''))
        if _f[1]&0x4000:
            os.chdir(_f[0])
            rlist('', level+1)
            os.chdir('..')
"""
