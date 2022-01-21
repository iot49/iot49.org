from controller import *
from param import PARAM

PARAM_DUTY1  = const(2)   # motor1 duty cycle setpoint
PARAM_DUTY2  = const(3)   # motor2 duty cycle setpoint

class Control(Controller):
    
    @staticmethod
    def fix_duty(duty):
        if abs(duty) > 1:
            duty = duty+8.5 if duty>0 else duty-8.5
        return duty

    def update(self):
        # set motor duty cycle
        self.state[STATE_DUTY1] = self.fix_duty(PARAM[PARAM_DUTY1])
        self.state[STATE_DUTY2] = self.fix_duty(PARAM[PARAM_DUTY2])
