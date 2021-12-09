class RPC_Test:
    
    def __init__(self, name):
        self._name = name
        
    def add(self, a, b):
        return "{}: {} + {} = {}".format(self._name, a, b, a+b)
    
    @property
    def name(self):
        return self._name
    
    def __str__(self):
        return "Demo {}".format(self._name)

