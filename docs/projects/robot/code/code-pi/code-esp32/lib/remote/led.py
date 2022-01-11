from machine import Pin, PWM
from time import sleep_ms

class LED:
    
    def __init__(self, pin_number):
        self._level = 0
        self.pwm = PWM(Pin(pin_number, mode=Pin.OUT), freq=1024)
        # for some reason this is needed?
        sleep_ms(10)
        self.pwm.duty(0)
        
    @property
    def level(self):
        return self._level
    
    @level.setter
    def level(self, l):
        if l<0: l = 0
        if l>1: l = 1
        self._level = l
        self.pwm.duty(int(1023*l))
        
    def deinit(self):
        self.pwm.deinit()
        self.pwm = None
        
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.deinit()
        
