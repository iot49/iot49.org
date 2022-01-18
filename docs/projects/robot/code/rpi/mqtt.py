from asyncio_mqtt import Client, ProtocolVersion
from struct import pack
import asyncio, json, os

import stm32
from robot import *

print(f"plot @ http://{os.getenv('DNS_NAME')}.local:5006")

MQTT_BROKER = os.getenv("HOST_IP")
TOPIC_ROOT = "public/vis"

PARAM_DUTY1  = const(PARAM_RESERVED+0)   # motor1 duty cycle setpoint
PARAM_DUTY2  = const(PARAM_RESERVED+1)   # motor2 duty cycle setpoint

class DutyControl:

    def __init__(self):
        pass

    async def main(self):
        async with Client(MQTT_BROKER, protocol=ProtocolVersion.V31) as client, \
            Comm(self.state_listener) as robot:
            self.client = client
            await client.publish(f"{TOPIC_ROOT}/new", json.dumps({
                "columns": [ "time [s]", "duty", "cpt" ],
                "rollover": 1000,
                "args": { "title": "Robot Motor" },
            }))
            # tests
            await robot.ping()
            await robot.echo('hello world')
            # robot
            await robot.set(PARAM_FS, 100)
            await robot.start('duty_control')
            for duty in [40, 80, 0]:
                await robot.set(PARAM_DUTY1, duty)
                await asyncio.sleep(1)

    async def state_listener(self, state):
        try:
            t = state[STATE_K]/PARAM[PARAM_FS]
            duty = state[STATE_DUTY1]
            cpt1 = state[STATE_CPT1]
            cpt2 = state[STATE_CPT2]
            dt1  = state[STATE_DT1]
            dt2  = state[STATE_DT2]
            await self.client.publish(f"{TOPIC_ROOT}/bin", pack('!3f', t, duty/100, cpt1))
        except Exception as e:
            print("*****", e)


dc = DutyControl()
asyncio.run(dc.main())