import asyncio
import sys

from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

# https://github.com/hbldh/bleak/blob/develop/examples/uart_service.py

class BLE_UART:
    
    UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
    UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

    # All BLE devices have MTU of at least 23. Subtracting 3 bytes overhead, we can
    # safely send 20 bytes at a time to any device supporting this service.
    UART_SAFE_SIZE = 20
    
    def __init__(self, peripheral_name='iot49-robot'):
        self._peripheral_name = peripheral_name
        self._rx_queue = asyncio.Queue()
        
    async def read(self):
        msg = await self._rx_queue.get()
        return msg
    
    async def write(self, msg):
        print("write disabled (install Bluez 5.51!)")
        return
        if isinstance(msg, str):
            msg = bytes(msg)
        await self._client.write_gatt_char(self.UART_RX_CHAR_UUID, msg)
        
    async def connect(self):
        self._discovery_queue = asyncio.Queue()
        device = None
        print(f"scanning for {self._peripheral_name}")
        async with BleakScanner(detection_callback=self._find_uart_device):
            device: BLEDevice = await self._discovery_queue.get()
        print(f"connecting to {self._peripheral_name} ...", end="")
        client = self._client = BleakClient(device, disconnected_callback=self._handle_disconnect)
        await client.connect()
        await client.start_notify(self.UART_TX_CHAR_UUID, self._rx_handler)    
        print(f" connected")
        
    async def disconnect(self):
        await self._client.disconnect()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.disconnect()
        
    def _rx_handler(self, _: int, data: bytearray):
        self._rx_queue.put_nowait(data)
    
    def _find_uart_device(self, device: BLEDevice, adv: AdvertisementData):
        # called whenever a device is detected during discovery
        # ignore all but target device
        print(f"_find_uart_device: {device.name}", device)
        if device.name == self._peripheral_name:
            self._discovery_queue.put_nowait(device)
        
    def _handle_disconnect(self, _: BleakClient):
        self._rx_queue.put_nowait(None)
