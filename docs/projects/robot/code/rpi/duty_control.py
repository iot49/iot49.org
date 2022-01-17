import asyncio
import stm32
from robot import *

PARAM_DUTY1  = const(2)   # motor1 duty cycle setpoint
PARAM_DUTY2  = const(3)   # motor2 duty cycle setpoint

async def main():
    async with Comm() as robot:
        # tests
        await robot.ping()
        await robot.echo('hello world')
        # parameter
        await robot.set(PARAM_FS, 2)
        await robot.set(PARAM_PWM, 10_000)
        print(f"fs  = {await robot.get(PARAM_FS)}")
        print(f"pwm = {await robot.get(PARAM_PWM)}")
        # start
        await robot.start('duty_control')
        # run robot
        for d in range(11):
            duty = 10*d
            await robot.set(PARAM_DUTY1, duty)
            print(f"duty1 = {await robot.get(PARAM_DUTY1)}")
            await asyncio.sleep(1)

asyncio.run(main())
