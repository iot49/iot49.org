import pyb

_uart = None

def get_uart():
    global _uart
    if not _uart:
        _uart = pyb.UART(6, baudrate=230400, read_buf_len=4096,
                        bits=8, parity=None, stop = 1, timeout=200, timeout_char=200)
    return _uart
