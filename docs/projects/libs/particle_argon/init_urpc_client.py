import board, busio


_uart = None

def get_uart():
    global _uart
    if not _uart:
        _uart = busio.UART(rx=board.ESP_RTS, tx=board.ESP_CTS, \
                          rts=board.ESP_HOST_WK, cts=board.ESP_BOOT_MODE, \
                          baudrate=1_000_000, timeout=30, receiver_buffer_size=2500)
    return _uart
