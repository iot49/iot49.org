# https://github.com/iot49/upy-examples/blob/master/encoder2.py

"""
Hardware quadrature encoder.
Works for Timers 2-5
  2 & 5 have 32-bit counters
  3 & 4 have 16-bit counters
Input is on ch1 & ch2.
  
Sample usage:

enc1 = init_encoder(3, Pin.cpu.A6, Pin.cpu.A7, Pin.AF2_TIM3)
enc2 = init_encoder(4, Pin.cpu.B6, Pin.cpu.B7, Pin.AF2_TIM4)

Readout (c2, 2's complement, only for 16-bit timers):
c2(enc1.counter())

Reset:
enc1.counter(0)
"""

from pyb import Pin, Timer

def init_encoder(timer, ch1_pin, ch2_pin, af):
    # sets up encoder and returns timer
    # read count by calling timer.counter()
    pin_a = Pin(ch1_pin, Pin.AF_PP, pull=Pin.PULL_NONE, af=af)
    pin_b = Pin(ch2_pin, Pin.AF_PP, pull=Pin.PULL_NONE, af=af)
    enc_timer = Timer(timer, prescaler=0, period=0xffff)
    enc_channel = enc_timer.channel(1, Timer.ENC_AB)
    return enc_timer


def c2(x):
    # two's complement of 16-Bit number
    if x & 0x8000:
        # two's complement of 16 bit value
        x -= 0x10000
    return x
    

def test_encoder(enc_timer):
    # connect CH1 pin to 'A0'
    #         CH2 pin to 'A1'
    # Usage: test_encoder(init_encoder(...))
    out_idx = 0
    out_seq = [0, 1, 3, 2]

    pin_a2 = Pin('A0', Pin.OUT_PP)
    pin_b2 = Pin('A1', Pin.OUT_PP)

    def set_out():
        print("    Writing   {:d}   {:d} ". \
              format((out_seq[out_idx] & 0x02) != 0, (out_seq[out_idx] & 0x01) != 0))
        pin_a2.value((out_seq[out_idx] & 0x01) != 0)
        pin_b2.value((out_seq[out_idx] & 0x02) != 0)

    def incr():
        nonlocal out_idx
        out_idx = (out_idx + 1) % 4
        set_out()

    def decr():
        nonlocal out_idx
        out_idx = (out_idx - 1) % 4
        set_out()

    print("                 ", end="")
    set_out()

    def show_count(prefix):
        nonlocal enc_timer
        cnt = c2(enc_timer.counter())

    for i in range(12):
        show_count('+')
        incr()
    for i in range(24):
        show_count('-')
        decr()
    for i in range(15):
        show_count('+')
        incr()
    show_count("Final")