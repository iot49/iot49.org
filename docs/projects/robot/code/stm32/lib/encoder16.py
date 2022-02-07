from pyb import Pin, Timer

"""
Encoder readout for STM32 16-bit timers. Corrects for counter over/under-flow.
"""

class Encoder16:
    
    def __init__(self, timer_no, ch1_pin, ch2_pin, af):
        pin_a = Pin(ch1_pin, Pin.AF_PP, pull=Pin.PULL_NONE, af=af)
        pin_b = Pin(ch2_pin, Pin.AF_PP, pull=Pin.PULL_NONE, af=af)
        timer = Timer(timer_no, prescaler=0, period=0xffff)
        channel = timer.channel(1, Timer.ENC_AB)
        self._timer = timer
        self._sum = 0
        self._cnt = timer.counter()
        
    def count(self):
        c = self._timer.counter()
        if c-self._cnt > 0x8fff:
            self._sum -= 0x10000
        if self._cnt-c > 0x8fff:
            self._sum += 0x10000
        self._cnt = c
        return self._sum + c


"""
Example:
        
enc = Encoder16(3, 'ENC_B1', 'ENC_B2', Pin.AF2_TIM3)

last = enc.count()
while True:
    c = enc.count()
    if abs(last-c) > 5:
        last = c
        print(f"{c:6d}")
"""