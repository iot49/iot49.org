from adafruit_blinka import Lockable

class I2C(Lockable):
    """
    Busio I2C Class for CircuitPython Compatibility. Used
    for both MicroPython and Linux.
    """

    def __init__(self, scl, sda, frequency=100000):
        """Initialization"""
        self.deinit()
        from machine import I2C as _I2C
        self._i2c = _I2C(1, freq=frequency)

    def deinit(self):
        """Deinitialization"""
        try:
            self._i2c.deinit()
            del self._i2c
        except AttributeError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.deinit()

    def scan(self):
        """Scan for attached devices"""
        return self._i2c.scan()

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        """Read from a device at specified address into a buffer"""
        if start != 0 or end is not None:
            if end is None:
                end = len(buffer)
            buffer = memoryview(buffer)[start:end]
        return self._i2c.readfrom_into(address, buffer)

    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        """Write to a device at specified address from a buffer"""
        if isinstance(buffer, str):
            buffer = bytes([ord(x) for x in buffer])
        if start != 0 or end is not None:
            if end is None:
                return self._i2c.writeto(address, memoryview(buffer)[start:], stop)
            return self._i2c.writeto(address, memoryview(buffer)[start:end], stop)
        return self._i2c.writeto(address, buffer, stop)

    def writeto_then_readfrom(
        self,
        address,
        buffer_out,
        buffer_in,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None,
        stop=False
    ):
        """ "Write to a device at specified address from a buffer then read
        from a device at specified address into a buffer
        """
        self.writeto(address, buffer_out, start=out_start, end=out_end, stop=stop)
        return self.readfrom_into(address, buffer_in, start=in_start, end=in_end)
    