import uasyncio as asyncio
import urpc_server
import machine

BAUDRATE = 230400

# maximum number of bytes returned by socket.readinto
READINTO_BUFFER_SIZE = 512

# WDT timeout [ms]
# Note: longest exec (urpc, mp) << WDT_TIMEOUT
WDT_TIMEOUT = 120000

# for Huzzah32 on top of STM32 feather
uart_config = { 'rx': 32, 'tx': 14, 'baudrate': BAUDRATE, 
                'rxbuf': 4096, 'txbuf': 1024 }

uart = machine.UART(2, **uart_config)
uart.init(bits=8, stop=2, parity=None, timeout=300)

async def wdt_feeder():
    wdt = machine.WDT(timeout=WDT_TIMEOUT)
    while True:
        await asyncio.sleep_ms(WDT_TIMEOUT // 3)
        wdt.feed()

async def blink():
    led = machine.Pin(13, mode=machine.Pin.OUT)
    while True:
        led.on()
        await asyncio.sleep(0.1)
        led.off()
        await asyncio.sleep(1.0)

async def main():
    asyncio.create_task(blink())
    asyncio.create_task(wdt_feeder())
    asyncio.create_task(urpc_server.async_serve(uart, READINTO_BUFFER_SIZE))
    asyncio.get_event_loop().run_forever()
    
asyncio.run(main())
