from . controller import *
from param import PARAM, PARAM_RESERVED
from pid import PID


P0 = const(2)
assert P0 == PARAM_RESERVED

SET_PITCH = const(P0+0)
KP        = const(P0+1)
KI        = const(P0+2)
KD        = const(P0+3)
U_MIN     = const(P0+4)
U_MAX     = const(P0+5)

PARAM[U_MIN] = -100
PARAM[U_MAX] =  100


class Control(Controller):
    
    def __init__(self, uart):
        super().__init__(uart)
        self.pid = PID(memoryview(PARAM)[SET_PITCH:U_MAX+1])
    
    def update(self):
        state = self.state
        pitch = state[STATE_PITCH]
        if abs(pitch) < 30:
            duty = self.pid.update(pitch)
            duty = self.fix_duty(duty)
        else:
            duty = 0
        state[STATE_DUTY1] = state[STATE_DUTY2] = duty
        
    @staticmethod
    def fix_duty(duty):
        if abs(duty) > 1:
            duty = duty+8.5 if duty>0 else duty-8.5
        return duty
