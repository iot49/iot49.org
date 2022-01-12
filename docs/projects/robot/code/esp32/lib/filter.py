class LPF1:
    
    def __init__(self, alpha=0.5, hysteresis=0.0):
        """
        First Order LPF.
        alpha = 0: no filtering
        increasing alpha increases the filter effect 
        until alpha = 1: input ignored
        """
        self._alpha = alpha
        self._hysteresis = hysteresis
        self._state = None
        
    @property
    def state(self):
        return self._state
    
    def update(self, input):
        """Update and return new state from input."""
        state = self._state
        if not state:
            state = input
        else:
            a = self._alpha
            state = a*state + (1-a)*input
        if abs(state) < self._hysteresis:
            state = 0
        self._state = state
        return state  

    
class Offset:
    
    def __init__(self):
        self.N = 0
        self.offset = None
        
    def update(self, value):
        """Update and return current offset"""
        self.N = N = self.N + 1
        if N == 1:           
            self.offset = value
        else:
            self.offset = ((N-1)*self.offset + value) / N
        return self.offset
    
