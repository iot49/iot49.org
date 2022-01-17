from controller import *
from param import PARAM

# Trivial "controller" that just turns on motors and sets pwm duty cycle.

PARAM_DUTY1  = const(2)   # motor1 duty cycle setpoint
PARAM_DUTY2  = const(3)   # motor2 duty cycle setpoint


class Control(Controller):

    def update(self):
        # set motor duty cycle
        self.state[STATE_DUTY1] = PARAM[PARAM_DUTY1]
        self.state[STATE_DUTY2] = PARAM[PARAM_DUTY2]
