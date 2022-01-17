import asyncio
import stm32
from robot import *


async def main():
    async with Comm(1_000_000) as robot:

        await robot.set(PARAM_FS, 5)
        await robot.ping()
        print(f"get(PARAM_FS) = {await robot.get(PARAM_FS):10.0f}")

        await robot.set(PARAM_FS, 7)
        print(f"get(PARAM_FS) = {await robot.get(PARAM_FS):10.0f}")

        # start
        await robot.start('duty_control')
        await asyncio.sleep(2)
        await robot.ping()        
        print("done!")

asyncio.run(main())
