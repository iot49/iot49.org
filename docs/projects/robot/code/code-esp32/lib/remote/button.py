from time import ticks_ms, ticks_diff
from machine import Pin

class Button:
    
    def __init__(self, pin, bounce_ms=200):
        self.count = 0
        self.pin = pin
        self._bounce_ms = bounce_ms
        self._last = ticks_ms()
        self._pressed = False
    
    @property
    def pressed(self):
        if self.pin.value() == 0 and ticks_diff(ticks_ms(), self._last) > self._bounce_ms:
            self._last = ticks_ms()
            self.count += 1
            return True
        return False
