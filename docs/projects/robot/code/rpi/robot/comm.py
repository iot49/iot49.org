from serial import Serial
from struct import pack, unpack
from array import array
import asyncio
import traceback
import time
import stm32
from . state import STATE, FS, EXEC_T
from . state import CMD_STATE, CMD_GET_ALL, CMD_GET, CMD_SET 
from . state import CMD_START, CMD_SHUTDOWN
from . state import CMD_PING, CMD_ECHO


class Comm:

    def __init__(self, state_listener=None, baudrate=1_000_000):
        stm32.hard_reset(quiet=True)
        self.baudrate = baudrate
        self.state_listener = state_listener

    async def __aenter__(self):
        # start program on MCU & listen for output
        tasks = []
        tasks.append(asyncio.create_task(self._repl(
            f"from robot import Robot\n"
            f"Robot({self.baudrate})\n"
        ), name="comm._repl"))
        await asyncio.sleep(1)
        self._uart = Serial(port='/dev/ttyAMA2', baudrate=self.baudrate, 
                            timeout=2, write_timeout=1, exclusive=False)
        self._resp_queue = asyncio.Queue()
        tasks.append(asyncio.create_task(self._cmd_response(), name="comm._cmd_response"))
        for task in tasks:
            task.add_done_callback(self._done_callback)
        self._tasks = tasks
        await asyncio.sleep(1)
        return self

    async def __aexit__(self, *args):
        for t in self._tasks: t.cancel()
        self._uart.write(bytes([CMD_SHUTDOWN]))
        self._uart.close()
        self._uart = None

    async def set(self, index, value):
        """Set state value"""
        self._uart.write(bytes([CMD_SET, index]))
        self._uart.write(pack('f', value))
        STATE[index] = value

    async def get(self, index):
        """Get state value"""
        self._uart.write(bytes([CMD_GET, index]))
        cmd, r = await self._resp_queue.get()
        assert CMD_GET == cmd, f"get: expected {CMD_GET}, got {cmd}"
        STATE[index] = r
        return r

    async def get_all(self):
        """Get all state values"""
        self._uart.write(bytes([CMD_GET_ALL]))
        cmd, r = await self._resp_queue.get()
        assert CMD_GET_ALL == cmd, f"get_all: expected {CMD_GET_ALL}, got {cmd}"
        assert len(r) == len(STATE), f"get_all: expected {len(STATE)} floats, got {len(r)}"
        for i, f in enumerate(r):
            STATE[i] = f

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

    async def ping_test(self):
        "Send ping & check response"
        self._uart.write(bytes([CMD_PING]))
        cmd, = await self._resp_queue.get()
        assert CMD_PING == cmd, f"ping: expected {CMD_PING}, got {cmd}"
        
    async def echo_test(self, msg):
        "Send message & check response"
        if isinstance(msg, str): msg = msg.encode()
        self._uart.write(bytes([CMD_ECHO, len(msg)]))
        self._uart.write(msg)
        cmd, r = await self._resp_queue.get()
        assert CMD_ECHO == cmd, f"echo: expected {CMD_ECHO}, got {cmd}"
        
    async def _cmd_response(self):
        """Receive and decode messages from stm32 & forward to destination."""
        uart = self._uart
        start = time.monotonic()
        Ts = 1/STATE[FS]
        while self._uart:
            if uart.in_waiting:
                t = uart.read(1)[0]
                if t == CMD_STATE:
                    # read the data
                    sz = uart.read(1)[0]
                    s = unpack(f"{sz}f", uart.read(4*sz))
                    # check execution time
                    _start = start
                    start = time.monotonic()
                    if start-_start > 1.1*Ts:
                        # skip this state update to give rpi time to catch up
                        # print(f"WARNING rpi: exec time {1e3*(start-_start):.0f}ms > Ts {1e3*Ts:.0f}ms")
                        continue
                    assert 1e-6*STATE[EXEC_T] < Ts, f"stm32: irq exec time {STATE[EXEC_T]:.0f}us > Ts"
                    STATE[0:len(s)] = array('f', s)
                    if self.state_listener: 
                        await self.state_listener()
                elif t == CMD_GET_ALL:
                    sz = uart.read(1)[0]
                    s = unpack(f"{sz}f", uart.read(4*sz))
                    await self._resp_queue.put((t, s))
                elif t == CMD_GET:
                    f = unpack('f', uart.read(4))[0]
                    await self._resp_queue.put((t, f))
                elif t == CMD_ECHO:
                    sz = uart.read(1)[0]
                    resp = uart.read(sz)
                    await self._resp_queue.put((t, resp))
                elif t in { CMD_SET, CMD_START, CMD_SHUTDOWN, CMD_PING }:
                    await self._resp_queue.put((t, ))
                else:
                    print(f"*** PI: unknown type: {t}")
                    # purge uart
                    while uart.in_waiting:
                        data = uart.read(uart.in_waiting)
                        try:
                            data = data.decode()
                        except:
                            pass
                        print("purging", data)
                        await asyncio.sleep(0.1)
            await asyncio.sleep(0)

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

    def _done_callback(self, task: asyncio.Task) -> None:
        try:
            print("task result", task.result())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"***** Task {task.get_name()}: {repr(e)}")
