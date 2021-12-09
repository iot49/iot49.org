import pyb, micropython

pyb.usb_mode('VCP')
micropython.alloc_emergency_exception_buf(100)
