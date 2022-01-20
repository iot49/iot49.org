from array import array

# Python port of https://github.com/br3ttb/Arduino-PID-Library

_R     = const(0)  # setpoint            
_U     = const(1)  # PID output             
_Y     = const(2)  # Last plant output        
_SUM   = const(3)  # Integral term       
_TS    = const(4)  # sampling interval [s]
_KP    = const(5)  # proportional term
_KI    = const(6)  # scaled by *Ts
_KD    = const(7)  # scaled by /Ts
_U_MIN = const(8)  # minimum PID output (anti-windup)
_U_MAX = const(9)  # maximum PID output (anti-windup)


class PID:
    
    def __init__(self, Ts, kp, ki, kd, u_min=-float('inf'), u_max=float('inf')):
        self.state = array('f', [
            0,     # r (setpoint)
            0,     # u (PID output)
            0,     # y (plant output)
            0,     # (integral sum for P-term calculation)
            Ts,    # sampling interval
            kp,    # kp
            ki*Ts, # ki scaled
            kd/Ts, # kd scaled
            u_min, # u_min
            u_max, # u_max
        ])
        
    def update(self, y):
        """compute new PID output u from plant output y"""
        s = self.state
        err = s[_R] - y
        s[_SUM] += self._clip(s[_KI] * err)   # integrator state
        u = self._clip(s[_KP] * err + s[_SUM] - s[_KD] * (y - s[_Y]))
        s[_Y] = y  # save last y
        return u
    
    def _clip(self, value):
        s = self.state
        if value > s[_U_MAX]: return s[_U_MAX]
        if value < s[_U_MIN]: return s[_U_MIN]
        return value

    @property
    def setpoint(self):
        return self.state[_R]
    
    @setpoint.setter
    def setpoint(self, setpoint):
        self.state[_R] = setpoint
        
    @property
    def kp(self):
        return self.state[_KP]
        
    @property
    def ki(self):
        return self.state[_KI] / self.state[_TS]
        
    @property
    def kd(self):
        return self.state[_KD] * self.state[_TS]
        
    @property
    def Ts(self):
        return self.state[_TS]
    
    @kp.setter
    def kp(self, kp):
        self.state[_KP] = kp
        
    @ki.setter
    def ki(self, ki):
        self.state[_KI] = ki * self.state[_TS]
        
    @kd.setter
    def kd(self, kd):
        self.state[_KD] = kd / self.state[_TS]
        
    @Ts.setter
    def Ts(self, Ts):
        state = self.state
        state[_KI] = state[_KI] * Ts / state[_TS]
        state[_KD] = state[_KD] / Ts * state[_TS]
        state[_TS] = Ts
    
    def set_limits(self, u_min, u_max):
        """PID output limits"""
        self.state[_U_MIN] = u_min
        self.state[_U_MAX] = u_max
