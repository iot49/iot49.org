import io

class State:
    
    # access to previous state object created 
    # used for differentiation e.g. of enc
    _last_state = None
    
    def __init__(self, rc, i_state, f_state):
        self.rc = rc
        self.i_state = i_state
        self.f_state = f_state
        self.last_state = State._last_state
        if not self.last_state: self.last_state = self
        State._last_state = self
        
    def get(self, name):
        try:
            i = self.rc.i_names.index(name)
            return self.i_state[i]
        except ValueError:
            pass
        try:
            i = self.rc.f_names.index(name)
            return self.f_state[i]
        except ValueError:
            pass
        if name == 'time [s]':
            return self.get('k')/self.rc.fs
        if name == 'diff_enc1':
            return self.get('enc1') - self.last_state.get('enc1')
        if name == 'diff_enc2':
            return self.get('enc2') - self.last_state.get('enc2')
        raise AttributeError(f"undefined: {name}")
            
    def __getattr__(self, name):
        return self.get(name)
    
    def __getitem__(self, name):
        return self.get(name)

    def __str__(self):
        names = [ 'time [s]' ] + self.rc.i_names + [ 'diff_enc1', 'diff_enc2' ] + self.rc.f_names
        s = io.StringIO()
        for name in names:
            s.write(f"{name} = {self.get(name)}\n")
        return s.getvalue()
    