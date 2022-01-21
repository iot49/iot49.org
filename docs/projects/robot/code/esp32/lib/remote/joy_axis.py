from machine import ADC, Pin
from time import sleep_ms

class JoyAxis:
    
    def __init__(self, pin, change_threshold=0.03, dead_zone=0.05):
        self._change_threshold = change_threshold
        self._dead_zone = dead_zone
        self._adc = adc = ADC(Pin(pin, mode=Pin.IN))
        adc.atten(ADC.ATTN_11DB)
        N = 10
        offset = 0
        for i in range(N):
            offset += adc.read()
            sleep_ms(10)
        self._offset = offset/N
        self._last = self.read()
        
    def read(self):
        # attempt to set range to +/-1
        F = 1450
        self._adc.read()
        return (self._adc.read()-self._offset)/F
    
    def read_changed(self):
        l = self._last
        v = self.read()
        # attempt to filter ESP32 ADC noise
        if abs(v) < self._dead_zone:
            v = 0
        if abs(v-l) < self._change_threshold:
            return None
        self._last = v
        return v
