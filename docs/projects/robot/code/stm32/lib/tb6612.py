"""
TB6612 motor driver.

Example:

from pyb import Pin, Timer
from tb6612 import TB6612
import time

freq = 10_000
tim = Timer(8, freq=freq)

motor1 = TB6612(
    tim.channel(3, Timer.PWM_INVERTED, pin=Pin('PWM_A')),
    Pin('AIN1', mode=Pin.OUT_PP),
    Pin('AIN2', mode=Pin.OUT_PP)
)

motor2 = TB6612(
    tim.channel(1, Timer.PWM_INVERTED, pin=Pin('PWM_B')),
    Pin('BIN1', mode=Pin.OUT_PP),
    Pin('BIN2', mode=Pin.OUT_PP)
)

nstby = Pin('NSTBY', mode=Pin.OUT_PP)
nstby.value(1)

motor1.speed(30)
motor2.speed(-83)

time.sleep(5)
nstby.value(0)
"""

class TB6612:
    
    def __init__(self, pwm, scale, in1, in2):
        self.pwm = pwm
        self.scale = scale
        self.in1 = in1
        self.in2 = in2
        
    def speed(self, speed:float):
        """Set motor speed (duty cycle), range +/- 100."""
        if speed < 0:
            self.in1.value(0)
            self.in2.value(1)
        else:
            self.in1.value(1)
            self.in2.value(0)
        speed *= self.scale
        self.pwm.pulse_width(int(abs(speed)))
