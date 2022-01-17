# comm.py

from param import *
from pyb import UART, disable_irq, enable_irq
from struct import pack
import gc, sys, time


class Comm:
    
    def __init__(self, baudrate):
        print(f"start Comm @ {baudrate} baud")
        self.uart = UART(3, baudrate, timeout=500)
        self._cmds()

    def _cmds(self):
        uart = self.uart
        # CMD_SET requires a memoryview
        param = memoryview(PARAM)
        controller = None
        while True:
            t = uart.readchar()
            if t < 0: continue    # timeout
            if t == CMD_GET:
                index = uart.readchar()
                disable_irq()
                uart.writechar(t)
                uart.write(pack('f', param[index]))
                enable_irq()
            elif t == CMD_SET:
                index = uart.readchar()
                uart.readinto(param[index:index+1])
            elif t == CMD_START:
                if controller: controller.shutdown()
                sz = uart.readchar()
                module = uart.read(sz)
                ctrl = getattr(__import__(module.decode()), "Control")
                controller = ctrl(uart)
            elif t == CMD_SHUTDOWN:
                if controller: controller.shutdown()
                controller = None
            elif t == CMD_PING:
                disable_irq()
                uart.writechar(t)
                enable_irq()
            elif t == CMD_ECHO:
                sz = uart.readchar()
                msg = uart.read(sz)
                disable_irq()
                uart.writechar(t)
                uart.writechar(len(msg))
                uart.write(msg)
                enable_irq()
            else:
                print(f"unknown command {t}")
