# comm.py

from pyb import UART, disable_irq, enable_irq
from array import array
from struct import pack
import gc, sys, time


CMD_STATE            = const(10)
CMD_MSG              = const(11)
CMD_SET_FSTATE       = const(12)
CMD_SET_KP           = const(13)
CMD_SET_KI           = const(14)
CMD_SET_KD           = const(15)
CMD_START_CONTROLLER = const(16)
CMD_STOP_CONTROLLER  = const(17)
CMD_SHUTDOWN         = const(18)

CMD_STATE_NAMES      = const(60)
CMD_ECHO             = const(61)
CMD_GET              = const(62)
CMD_PING             = const(63)


class Comm:
    
    def __init__(self, baudrate=1_000_000, pwm_freq=10_000):
        self.uart = UART(3, baudrate, timeout=500)
        try:
            # recursive import
            from controller import Controller
            print("init controller")
            self.controller = Controller(self.uart, pwm_freq)
            self.cmd_handler()
        except Exception as e:
            print("***** Comm {}".format(e))
            sys.print_exception(e, self.uart)
    
    def cmd_handler(self):
        """Handle commands from host"""
        uart = self.uart
        # preallocate
        _i1 = array('i', [0])
        _f1 = array('f', [0])
        while True:
            t = uart.readchar()
            if t < 0: continue
            # print("cmd_handler t = {}".format(t))
            if t == CMD_SET_FSTATE:
                index = uart.readchar()
                uart.readinto(_f1)
                self.controller.f_state[index] = _f1[0]
            elif t == CMD_SET_KP:
                index = uart.readchar()
                uart.readinto(_f1)
                self.controller.set_kp(index, _f1[0])
            elif t == CMD_SET_KI:
                index = uart.readchar()
                uart.readinto(_f1)
                self.controller.set_ki(index, _f1[0])
            elif t == CMD_SET_KD:
                index = uart.readchar()
                uart.readinto(_f1)
                self.controller.set_kd(index, _f1[0])
            elif t == CMD_STATE_NAMES:
                import controller
                disable_irq()
                uart.writechar(CMD_STATE_NAMES)
                buf = repr(controller.INAMES).encode()
                uart.write(pack('H', len(buf)))
                uart.write(buf)
                buf = repr(controller.FNAMES).encode()
                uart.write(pack('H', len(buf)))
                uart.write(buf)
                enable_irq()
            elif t == CMD_GET:
                index = uart.readchar()
                disable_irq()
                uart.writechar(CMD_GET)
                uart.write(pack('f', self.controller.f_state[index]))
                enable_irq()
            elif t == CMD_START_CONTROLLER:
                uart.readinto(_i1)
                fs = _i1[0]
                uart.readinto(_i1)
                cb_name = uart.read(_i1[0]).decode()
                self.controller.start(fs, cb_name)
            elif t == CMD_STOP_CONTROLLER:
                self.controller.stop()
            elif t == CMD_SHUTDOWN:
                self.controller.shutdown()
            elif t == CMD_PING:
                disable_irq()
                uart.writechar(CMD_PING)
                enable_irq()                
            elif t == CMD_ECHO:
                uart.readinto(_i1)
                buf = uart.read(_i1[0])
                disable_irq()
                uart.writechar(CMD_ECHO)
                uart.write(_i1)
                uart.write(buf)
                enable_irq()
            else:
                self.send_msg("***** Invalid msg type: {}".format(t))

    def send_msg(self, msg):
        """Send a message (bytes or str) to host"""
        if isinstance(msg, str): msg = msg.encode()
        uart = self.uart
        disable_irq()
        uart.writechar(CMD_MSG)
        uart.write(pack('H', len(msg)))
        uart.write(msg)
        enable_irq()

    def shutdown(self):
        """Turn off motors, return to REPL"""
        self.nstby.value(0)
        self.c_timer.deinit()
        self.uart.init(115200)
