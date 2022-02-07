from .ble_uart import BLE_UART
from struct import pack, unpack
import asyncio, time, os

# fix robot wiring issue (if there is one?)
if os.getenv('BALENA_DEVICE_ARCH') == 'aarch64':
    try:
        from gpiozero import Button as Pin
        Pin(14, pull_up=False)
    except:
        pass


class Remote:
    
    def __init__(self, event_handler=None):
        self.stop = False
        self._event_handler = event_handler
        
    def shutdown(self, code: str):
        """Called if remote disconnects - turned off (code='q') or connection lost ('d').
        Overload in derived class.
        After this call, self.run returns.
        """
        if code == 'q':
            print("-"*10, "Remote powered down - QUIT!")
        elif code == 'd':
            print("-"*10, "Remote disconnected!")
            
    async def timeout(self):
        """Called in case of timeout (no timely hartbeat received).
        Default action is disconnect and shutdown.
        Overload in derived class if different action is required (e.g. turn off motors).
        """
        print("timeout")
        await self.disconnect()
        
    async def disconnect(self):
        """Disconnect & shut down."""
        print("disconnect")
        self.stop = True

    async def _recv(self):
        while not self.stop:
            try:
                data = await asyncio.wait_for(self.uart.read(), timeout=2)
                if data == None: 
                    code, value = ('d', 0)      
                else:
                    code, value = unpack('>Bf', data)
                    code = chr(code)
                if self._event_handler:
                    await self._event_handler(code, value)
                if code == 'q' or code == 'd':
                    self.shutdown(code)
                    break
            except asyncio.TimeoutError:
                await self.timeout()
        self.stop = True
                
    async def rgb(self, *, r=None, g=None, b=None):
        """LED on/off, 1/0 or None for no change"""
        uart = self.uart
        try:
            if r != None: await uart.write(pack('>Bf', ord('R'), r))
            if g != None: await uart.write(pack('>Bf', ord('G'), g))
            if b != None: await uart.write(pack('>Bf', ord('B'), b))
        except Exception as e:
            print(f"***** remote.rgb: {e}")
            
    async def __aenter__(self):
        self.uart = BLE_UART('iot49-robot')
        await self.uart.connect()
        self._recv_task = asyncio.create_task(self._recv(), name="remote._recv")
        self._recv_task.add_done_callback(self._done_callback)
        return self

    async def __aexit__(self, *args):
        self._recv_task.cancel()
        await self.uart.disconnect()
        return self

    def _done_callback(self, task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"***** Task {task.get_name()}: {repr(e)}")
