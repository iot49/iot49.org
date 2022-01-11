from .ble_uart import BLE_UART
from struct import pack, unpack
import asyncio, time


class Remote:
    
    def __init__(self):
        self.stop = False
        
    async def handle(self, dt: float, code: str, value: float):
        """Handle message received from BLE. 
        Overload in derived class.
        @param dt: time [s] since last message
        @param code: character code of message
        @param value: value of message
        """
        if code != 'h':
            if dt < 0.01: print(f"***** QUICK READ:  {1000*dt:12.8} [ms]")
            print(f"RECV {code} = {value:8.3f}   dt = {1000*dt:12.4} [ms]")
            
    async def shutdown(self, dt: float, code: str):
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
        last_rx = time.monotonic()
        while not self.stop:
            try:
                data = await asyncio.wait_for(self.uart.read(), timeout=1)
                dt = time.monotonic() - last_rx
                last_rx = time.monotonic()
                if data == None: 
                    code = 'd'      
                else:
                    code, value = unpack('>Bf', data)
                    code = chr(code)
                if code == 'q' or code == 'd':
                    await self.shutdown(dt, code)
                    break
                else:
                    await self.handle(dt, code, value)
            except asyncio.TimeoutError:
                await self.timout()
        self.stop = True
                
    async def rgb(self, r=None, g=None, b=None):
        """LED level, 0 ... 1 or None for no change"""
        uart = self.uart
        if r: await uart.write(pack('>Bf', ord('R'), r))
        if g: await uart.write(pack('>Bf', ord('G'), g))
        if b: await uart.write(pack('>Bf', ord('B'), b))
            
            
    async def run(self, peripheral_name='mpy-uart'):
        """Sample main"""
        async with BLE_UART(peripheral_name) as uart:
            self.uart = uart
            await uart.connect()
            asyncio.create_task(self._recv())
            while not self.stop:
                await asyncio.sleep(0.5)
            print("so long ...")
            try:
                await uart.disconnect()
            except Exception as e:
                print("# disconnect barfed", type(e))
                        