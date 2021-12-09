from machine import Pin, ADC
import time
        
class Scale:
    
    def __init__(self, out_pin=39, ref_pin=34, scale=500/840):
        self._out = ADC(Pin(out_pin))
        self._out.atten(ADC.ATTN_11DB)
        self._ref = ADC(Pin(ref_pin))
        self._ref.atten(ADC.ATTN_11DB)
        self._scale = scale
        self._offset = self._read_adc()
    
    def _read_adc(self, N=100):
        sum = 0
        out = self._out
        ref = self._ref
        for _ in range(N):
            sum += out.read() - ref.read()
        return sum/N
            
    def measure(self):
        return (self._read_adc()-self._offset) * self._scale
    
    def tare(self, button):
        print("tare")
        self._offset = self._read_adc()
