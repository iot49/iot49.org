import uasyncio as asyncio
import socket
from mp import async_server
 
    
async def blink():
    from digitalio import DigitalInOut
    from board import RGB_LED_BLUE as LED
    led = DigitalInOut(LED)
    led.switch_to_output()
    while True:
        led.value = False
        await asyncio.sleep(0.1)
        led.value = True
        await asyncio.sleep(1.0)

async def main():
    asyncio.create_task(blink())
    await async_server.start_async_server()
    asyncio.get_event_loop().run_forever()

asyncio.run(main())