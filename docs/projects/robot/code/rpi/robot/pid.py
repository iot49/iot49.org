# Based on https://github.com/br3ttb/Arduino-PID-Library

from array import array

try:
    _ = const(0)
except NameError:
    def const(x): return x


# config vector (may be dynamically updated)

SETPOINT  = const(0)  # setpoint            
KP        = const(1)  # proportional term
KI        = const(2)  # scaled by /fs
KD        = const(3)  # scaled by *fs
U_MIN     = const(4)  # minimum PID output (anti-windup)
U_MAX     = const(5)  # maximum PID output (anti-windup)
_SUM      = const(6)  # internal (KI term)
_Y        = const(7)  # internal (KD term)

STATE_LEN = _Y+1

class PID:
    
    def __init__(self, config):
        self.config = config
    
    def update(self, y):
        """compute & return new PID output u from plant output y"""
        c = self.config
        err = c[SETPOINT] - y
        c[_SUM] += self._clip(c[KI] * err)   # integrator state
        u = self._clip(c[KP] * err + c[_SUM] - c[KD] * (y - c[_Y]))
        c[_Y] = y   # save last y (for KD term)
        return u
    
    def _clip(self, value):
        c = self.config
        if value > c[U_MAX]: return c[U_MAX]
        if value < c[U_MIN]: return c[U_MIN]
        return value
