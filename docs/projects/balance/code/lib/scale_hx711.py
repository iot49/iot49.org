from hx711 import HX711
from machine import Pin
        
class ScaleHX711:
    
    def __init__(self, data_pin=12, clock_pin=27, scale=500/1059800):
        self._scale = scale
        pin_OUT = Pin(data_pin, Pin.IN, pull=Pin.PULL_DOWN)
        pin_SCK = Pin(clock_pin, Pin.OUT)
        self._hx711 = hx = HX711(pin_SCK, pin_OUT)
        hx.tare(20)
        hx.set_time_constant(0.25)
        
    @property
    def hx711(self):
        return self._hx711
    
    def measure(self, N=10):
        hx = self._hx711
        v = 0
        for _ in range(N):
            v += hx.get_value()
        v /= N
        return v * self._scale
    
    def tare(self, button):
        self.hx711.tare(20)
