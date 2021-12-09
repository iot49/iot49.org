import pyb, micropython

pyb.usb_mode('VCP')
micropython.alloc_emergency_exception_buf(100)

from machine import SPI, Pin
from flash_spi import FLASH
import os, sys

spi = SPI(1, baudrate=10_000_000, polarity=1, phase=1)
cspins = (Pin('FLASH_CS', Pin.OUT, value=1),)
flash = FLASH(spi, cspins)

os.mount(flash, "/spi")

sys.path.append('/spi')
sys.path.append('/spi/lib')

try:
    import start
except ImportError:
    pass