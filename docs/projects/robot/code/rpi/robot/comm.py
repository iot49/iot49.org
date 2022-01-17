from serial import Serial
from struct import pack, unpack
import numpy as np
import asyncio
import stm32
from . param import *

# fix wiring issue
from gpiozero import Button as Pin
Pin(14, pull_up=False)

# state
STATE_K      = const(0)    # normalized time
STATE_PITCH  = const(1)    # pitch angle [degree]
STATE_CPT1   = const(2)    # encoder1 counts in last cycle
STATE_CPT2   = const(3)    # encoder1 counts in last cycle
STATE_DUTY1  = const(4)    # motor1 duty cycle, +/- 100
STATE_DUTY2  = const(5)    # motor2 duty cycle, +/- 100
STATE_DT1    = const(6)    # controller exec time [us]
STATE_DT2    = const(7)    # controller + state comm of _last_ cycle time [us]


class Comm:

    def __init__(self, baudrate=1_000_000):
        stm32.hard_reset()
        self.baudrate = baudrate

    async def __aenter__(self):
        # start program on MCU & listen for output
        asyncio.create_task(self._repl(
            f"from comm import Comm\n"
            f"Comm({self.baudrate})\n"
        ))
        await asyncio.sleep(1)
        # communications port
        self._uart = Serial(port='/dev/ttyAMA2', baudrate=self.baudrate, 
                            timeout=2, write_timeout=1, exclusive=False)
        self._resp_queue = asyncio.Queue()
        self._cmd_response_task = asyncio.create_task(self._cmd_response())
        return self

    async def __aexit__(self, *args):
        self._cmd_response_task.cancel()
        self._uart.write(bytes([CMD_SHUTDOWN]))
        self._uart.close()
        self._uart = None

    async def _repl(self, cmd, dev='/dev/ttyAMA1'):
        stm32.exec_no_follow(cmd)
        with Serial(dev, 115200, timeout=0.5, write_timeout=2, exclusive=False) as serial:
            while True:
                if serial.in_waiting:
                    data = serial.read(serial.in_waiting)
                    try:
                        data = data.decode()
                        data = data.replace('\n', '\n     ')
                    except:
                        pass
                    print(f"MCU: {data}")
                    await asyncio.sleep(0)
                else:
                    await asyncio.sleep(0.5)

    async def set(self, index, value):
        self._uart.write(bytes([CMD_SET, index]))
        self._uart.write(pack('f', value))

    async def get(self, index):
        self._uart.write(bytes([CMD_GET, index]))
        cmd, r = await self._resp_queue.get()
        assert cmd == CMD_GET, f"ping: expected {CMD_GET}, got {cmd}"
        return r

    async def start(self, controller='duty_control'):
        if isinstance(controller, str): controller = controller.encode()
        self._uart.write(bytes([CMD_START, len(controller)]))
        self._uart.write(controller)

    async def shutdown(self):
        self._uart.write(bytes([CMD_SHUTDOWN]))

    async def ping(self):
        "Send ping & check response"
        self._uart.write(bytes([CMD_PING]))
        cmd, = await self._resp_queue.get()
        assert cmd == CMD_PING, f"ping: expected {CMD_PING}, got {cmd}"
        
    async def echo(self, msg):
        "Send message & check response"
        if isinstance(msg, str): msg = msg.encode()
        self._uart.write(bytes([CMD_ECHO, len(msg)]))
        self._uart.write(msg)
        cmd, r = await self._resp_queue.get()
        assert cmd == CMD_ECHO, f"echo: expected {CMD_ECHO}, got {cmd}"
        
    async def _cmd_response(self):
        """Receive and decode messages from stm32 & forward to destination."""
        uart = self._uart
        resp_queue = self._resp_queue
        while True:
            if uart.in_waiting:
                t = uart.read(1)[0]
                # print(f"_cmd_response {t}")
                if t == CMD_STATE:
                    sz = uart.read(1)[0]
                    s = np.frombuffer(uart.read(4*sz), dtype=np.float32)
                    print(f"CMD_STATE = ", end="")
                    for f in s:
                        print(int(f), end=" ")
                    print(f"pitch={s[STATE_PITCH]:.2f}")
                elif t == CMD_GET:
                    f = unpack('f', uart.read(4))[0]
                    await resp_queue.put((t, f))
                elif t == CMD_PING:
                    await resp_queue.put((t, ))
                elif t == CMD_ECHO:
                    sz = uart.read(1)[0]
                    resp = uart.read(sz)
                    await resp_queue.put((t, resp))
                else:
                    print(f"*** PI: unknown type: {t}")
                    # purge uart
                    while uart.in_waiting:
                        data = uart.read(uart.in_waiting)
                        try:
                            data = data.decode()
                        except:
                            pass
                        print(data)
                        await asyncio.sleep(0.1)
            await asyncio.sleep(0.1)
