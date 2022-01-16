# comm.py

from state import STATE
from pyb import UART, disable_irq, enable_irq
from struct import pack
import gc, sys, time

# possible optimization:
# replace with literal copy of CMD_* 
from state import *

class Comm:
    
    def __init__(self, baudrate):
        print(f"start Comm @ {baudrate} baud")
        self.uart = UART(3, baudrate, timeout=500)
        self.cmd_handler()

    def cmd_handler(self):
        uart = self.uart
        smv = memoryview(STATE)
        while True:
            t = uart.readchar()
            if t < 0: continue    # timeout
            # BEGIN CRITICAL SECTION: uart.write, STATE
            disable_irq()
            if t == CMD_GET:
                index = uart.readchar()
                uart.writechar(t)
                uart.write(pack('f', smv[index]))
            elif t == CMD_SET:
                index = uart.readchar()
                uart.readinto(smv[index:index+1])
            elif t == CMD_SHUTDOWN:
                print("shutdown")
            elif t == CMD_PING:
                uart.writechar(t)
            elif t == CMD_ECHO:
                sz = uart.readchar()
                msg = uart.read(sz)
                uart.writechar(t)
                uart.writechar(len(msg))
                uart.write(msg)
            else:
                print(f"unknown command {t}")
            # END CRITICAL SECTION
            enable_irq()
