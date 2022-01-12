from .state import State
from stm32 import async_repl

from iot_device.pydevice import Pydevice
          
from serial import Serial
from struct import pack, unpack
import numpy as np
import asyncio, time, queue


def const(x): return x

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

PID_CPT1             = const(0)
PID_CPT2             = const(1)


class RobotComm:
    
    def __init__(self, *, pwm_freq=10_000, baudrate=1_000_000):
        self.pwm_freq = pwm_freq
        self.baudrate = baudrate
        
    @property
    def i_names(self):
        return self._inames
        
    @property
    def f_names(self):
        return self._fnames
    
    def set_fstate(self, name, value):
        self._set_xxx(CMD_SET_FSTATE, self._fnames.index(name), value)
        
    def set_kp(self, pid_index, value):
        self._set_xxx(CMD_SET_KP, pid_index, value)
            
    def set_ki(self, pid_index, value):
        self._set_xxx(CMD_SET_KI, pid_index, value)
            
    def set_kd(self, pid_index, value):
        self._set_xxx(CMD_SET_KD, pid_index, value)
        
    def start_controller(self, fs, name):
        if isinstance(name, str): name = name.encode()
        self._send_cmd(CMD_START_CONTROLLER)
        self._uart.write(pack('2I', fs, len(name)))
        self._uart.write(name)
            
    def stop_controller(self):
        self._send_cmd(CMD_STOP_CONTROLLER)

    def get_state_queue(self) -> queue.Queue:
        """Read state queue from MCU
        Note: Bokeh runs in separate thread, hence asyncio.Qeueu cannot be used.
        """
        return self._state_queue
    
    async def ping(self):
        self._ping_event = asyncio.Event()
        self._send_cmd(CMD_PING)
        await self._ping_event.wait()        
        
    async def echo_test(self, msg):
        if isinstance(msg, str): msg = msg.encode()
        self._echo_queue = asyncio.Queue()
        self._send_cmd(CMD_ECHO)
        self._uart.write(pack('I', len(msg)))
        self._uart.write(msg)
        echo = await self._echo_queue.get()
        assert echo == msg, f"echo: {echo} != {msg}"
        return True
        
    async def __aenter__(self):
        # start program on MCU
        repl_task = async_repl(
                # f"print('foo')\n"
                # f"for i in range(20):\n"
                # f"    print(i)\n"
                f"from comm import Comm\n"
                f"Comm({self.baudrate}, {self.pwm_freq})\n"
            )
        asyncio.create_task(repl_task)
        self._uart = Serial(port='/dev/ttyAMA2', baudrate=self.baudrate, 
                            timeout=2, write_timeout=1, exclusive=False)
        await asyncio.sleep(1)
        self._cmd_processor_task = asyncio.create_task(self._cmd_processor())
        self._send_cmd(CMD_STATE_NAMES)
        await self.ping()
        return self

    async def __aexit__(self, *args):
        self._cmd_processor_task.cancel()
        self._send_cmd(CMD_SHUTDOWN)
        self._uart.close()
        self._uart = None
        
    async def _cmd_processor(self):
        """Process commands initiated by MCU"""
        uart = self._uart
        state_queue = self._state_queue = queue.Queue()
        State._last_state = None
        while True:
            if uart.in_waiting:
                t = uart.read(1)[0]
                # print("cmd", t)
                if t == CMD_MSG:
                    size = unpack('H', uart.read(2))[0]
                    print(f"> {(uart.read(size)).decode()}")
                elif t == CMD_STATE_NAMES:
                    size = unpack('H', uart.read(2))[0]
                    self._inames = eval(uart.read(size))
                    size = unpack('H', uart.read(2))[0]
                    self._fnames = eval(uart.read(size))
                elif t == CMD_STATE:
                    i_state = np.frombuffer(uart.read(4*len(self.i_names)), dtype=np.int32)
                    f_state = np.frombuffer(uart.read(4*len(self.f_names)), dtype=np.float32)
                    state_queue.put_nowait(State(self, i_state, f_state))
                elif t == CMD_PING:
                    self._ping_event.set()
                elif t == CMD_ECHO:
                    sz = unpack('I', uart.read(4))[0]
                    echo = uart.read(sz)
                    self._echo_queue.put_nowait(echo)
                else:
                    print(f"*** unknown type: {t}")
                    # purge uart
                    while uart.in_waiting:
                        data = uart.read(uart.in_waiting)
                        try:
                            data = data.decode()
                        except:
                            pass
                        print(data)
                        await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.1)
                
    def _set_xxx(self, cmd, index, value):
        self._send_cmd(cmd)
        self._uart.write(bytes([index]))
        self._uart.write(pack('f', value))

    def _send_cmd(self, cmd):
        self._uart.write(bytes([cmd]))
