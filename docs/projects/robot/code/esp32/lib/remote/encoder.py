class Encoder:
    
    CODE = [0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0]
    
    def __init__(self, pin1, pin2):
        self.count = 0
        self._quarter = 0
        self._state = 0
        self.pin1 = pin1
        self.pin2 = pin2
        pin1.irq(self.cb)
        pin2.irq(self.cb)
        
    def reset(self):
        self.count = 0
        self._quarter = 0
        self._state = 0        
            
    def cb(self, pin):
        new_state = self.pin1()
        new_state = (new_state << 1) + (new_state ^ self.pin2())
        
        change = (new_state - self._state) & 0x03
        if change == 1:
            self._quarter += 1
        elif change == 3:
            self._quarter -= 1
        self._state = new_state
        
        if self._quarter >= 4:
            self.count += 1
            self._quarter = 0
        elif self._quarter <= -4:
            self.count -= 1
            self._quarter = 0
