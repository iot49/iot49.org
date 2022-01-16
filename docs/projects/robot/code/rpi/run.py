import asyncio
import stm32
from robot import Comm

def exception_handler(loop, context):
    msg = context.get("exception", context["message"])
    print("***** asyncio:", context)
    print("***** msg:", msg)

asyncio.get_event_loop().set_exception_handler(exception_handler)

stm32.hard_reset()

async def main():
    async with Comm(1_000_000) as robot:
        print("ping")
        await robot.ping()
        print("echo")
        await robot.echo('hello world')
        print(f"get(2) = {await robot.get(2)}")
        print("set")
        await robot.set(2, 2.7)
        print(f"get(2) = {await robot.get(2)}")


asyncio.run(main())
