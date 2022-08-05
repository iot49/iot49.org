from robot import STATE, DUTY_CM, DUTY_DEAD, TACHO_CM, PID_TACH_CM
from robot import Controller, PID
from robot import SETPOINT, KP

class Control(Controller):
    
    def __init__(self, uart):
        super().__init__(uart)
        self.dz  = STATE[DUTY_DEAD]
        self.pid = PID(memoryview(STATE)[PID_TACH_CM:])
        
    def update(self):
        duty = self.pid.update(STATE[TACHO_CM])
        STATE[DUTY_CM] = self.fix_duty(duty)
    
    def fix_duty(self, duty):
        if abs(duty) > 0.5:
            DZ = self.dz
            return duty+DZ if duty>0 else duty-DZ
        return 0
