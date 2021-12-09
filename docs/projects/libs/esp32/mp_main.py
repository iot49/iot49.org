import uasyncio as asyncio
from mp import async_server

async def blink():
    import machine
    led = machine.Pin(13, mode=machine.Pin.OUT)
    while True:
        led.on()
        await asyncio.sleep(0.1)
        led.off()
        await asyncio.sleep(1.0)

async def main():
    asyncio.create_task(blink())
    await async_server.start_async_server()
    asyncio.get_event_loop().run_forever()

asyncio.run(main())