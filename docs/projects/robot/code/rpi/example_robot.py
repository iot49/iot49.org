from robot import AbstractRobot
import numpy as np
import asyncio
import traceback

class ExampleRobot(AbstractRobot):

    BLE_PID = 'TACH_CM'   
    BLE_X   = 'DUTY_CM'
    BLE_Y   = 'DUTY_DIFF'
    
    async def ble_event(self, code: str, value: float):
        # print(f"ble_event: {code} {value:8.2f}")
        if code == 'x':
            cm = await self.get(BLE_Y)
            df = abs(100-abs(cm))
            await self.set(BLE_X, df*value)
        if code == 'y':
            await self.set(BLE_Y, 80*value)
        if value < 0:
            value = 0
        if code == '1':
            await self.set_pid(self.BLE_PID, 'KP', 0.01*value)
        if code == '2':
            await self.set_pid(self.BLE_PID, 'KI', 0.01*value)
        if code == '3':
            await self.set_pid(self.BLE_PID, 'KD', 0.01*value)
        if code == 'd' or code == 'q':
            self.stop = True

    async def new_plot(self):
        cols = [ 'time [s]', 'duty cm', 'duty diff', 'tacho cm', 'tacho diff' ]
        return {
            "columns": cols,
            "rollover": 10 * await self.get('FS'),
            "layout": "line_plot",
            "args": { 
                "title": f"ExampleRobot",
                "plot_width": 1200,
                "plot_height": 700,
                # "y_range": (-150, 150),
            },
        }

    async def update_plot(self):
        return [ await self.get('K') / await self.get('FS'),
                 await self.get('DUTY_CM'),
                 await self.get('DUTY_DIFF'),
                 await self.get('TACHO_CM'),
                 await self.get('TACHO_DIFF') ]


def asyncio_exception(loop, context):
    msg = context.get("exception", context["message"])
    print(f"***** asyncio: {msg}")
    traceback.format_exc()


async def example_main():
    asyncio.get_event_loop().set_exception_handler(asyncio_exception)

    # spin motor 1
    async with ExampleRobot() as robot:
        # verify communication with stm32
        await robot.ping_test()
        await robot.echo_test()
        # set parameter values
        await robot.set('FS', 100)
        await robot.set('PWM_FREQ', 10_000)
        # verify that state on stm32 and rpi is idential
        await robot.check_state()   
        # start
        await robot.start()
        for duty in np.linspace(0, 100, 5):
            await robot.set('DUTY_CM', duty)
            await asyncio.sleep(1)

    # remote control: joystick mapped to motor duty cycle
    async with ExampleRobot(enable_remote=True) as robot:
        await robot.start()


def main():
    try:
        asyncio.run(example_main())
    except KeyboardInterrupt:
        print("so long")

if __name__ == "__main__":
    main()
    