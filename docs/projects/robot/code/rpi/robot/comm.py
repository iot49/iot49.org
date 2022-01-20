from serial import Serial
from struct import pack, unpack
import numpy as np
import asyncio
import stm32
from . param import *

# fix wiring issue
from gpiozero import Button as Pin
Pin(14, pull_up=False)



class Comm:

    def __init__(self, state_listener=None, baudrate=1_000_000):
        print("reset stm32")
        stm32.hard_reset()
        self.baudrate = baudrate
        self.state_listener = state_listener

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

    async def set(self, index, value):
        """Set parameter value"""
        self._uart.write(bytes([CMD_SET, index]))
        self._uart.write(pack('f', value))
        PARAM[index] = value

    async def get(self, index):
        """Get parameter value"""
        self._uart.write(bytes([CMD_GET, index]))
        cmd, r = await self._resp_queue.get()
        assert CMD_GET == cmd, f"get: expected {CMD_GET}, got {cmd}"
        PARAM[index] = r
        return r

    async def start(self, controller='duty_control'):
        """Start controller."""
        if isinstance(controller, str): controller = controller.encode()
        self._uart.write(bytes([CMD_START, len(controller)]))
        self._uart.write(controller)
        cmd, = await self._resp_queue.get()
        assert CMD_START == cmd, f"start: expected {CMD_START}, got {cmd}"

    async def shutdown(self):
        """Shutdown turn off motors and shutdown controller."""
        self._uart.write(bytes([CMD_SHUTDOWN]))

    async def ping(self):
        "Send ping & check response"
        self._uart.write(bytes([CMD_PING]))
        cmd, = await self._resp_queue.get()
        assert CMD_PING == cmd, f"ping: expected {CMD_PING}, got {cmd}"
        
    async def echo(self, msg):
        "Send message & check response"
        if isinstance(msg, str): msg = msg.encode()
        self._uart.write(bytes([CMD_ECHO, len(msg)]))
        self._uart.write(msg)
        cmd, r = await self._resp_queue.get()
        assert CMD_ECHO == cmd, f"echo: expected {CMD_ECHO}, got {cmd}"
        
    async def _cmd_response(self):
        """Receive and decode messages from stm32 & forward to destination."""
        uart = self._uart
        resp_queue = self._resp_queue
        state_listener = self.state_listener
        while uart:
            if uart.in_waiting:
                t = uart.read(1)[0]
                if t == CMD_STATE:
                    sz = uart.read(1)[0]
                    s = np.frombuffer(uart.read(4*sz), dtype=np.float32)
                    if state_listener: 
                        await state_listener(s)
                elif t == CMD_GET:
                    f = unpack('f', uart.read(4))[0]
                    await resp_queue.put((t, f))
                elif t == CMD_ECHO:
                    sz = uart.read(1)[0]
                    resp = uart.read(sz)
                    await resp_queue.put((t, resp))
                elif t in { CMD_SET, CMD_START, CMD_SHUTDOWN, CMD_PING }:
                    await resp_queue.put((t, ))
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
            await asyncio.sleep(0.001)

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
