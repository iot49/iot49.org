
from machine import Pin
import time

class Button:
    
    def __init__(self, pin, handler, debounce_ms=100):
        self._handler = handler
        self._debounce_ms = debounce_ms
        self._last_press = 0
        button = Pin(pin, mode=Pin.IN, pull=Pin.PULL_UP)
        button.irq(handler=self._irq, trigger=Pin.IRQ_FALLING)
        
    def _irq(self, button):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_press) < self._debounce_ms:
            return
        self._last_press = now
        self._handler(button)
