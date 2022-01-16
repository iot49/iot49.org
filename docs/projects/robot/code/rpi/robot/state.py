from array import array

try:
    const(0)
except NameError:
    def const(x): return x


#commands

CMD_GET      = const(1)
CMD_SET      = const(2)
CMD_SHUTDOWN = const(3)
CMD_PING     = const(4)
CMD_ECHO     = const(5)


# shared state vector

S_K          = const(0)
S_DT1        = const(1)
S_DT2        = const(2)
S_CPT1       = const(3)
S_CPT2       = const(4)
S_PITCH      = const(5)
S_DUTY1      = const(6)
S_DUTY2      = const(7)

S_LEN        = const(8)

STATE = array('f', [0]*S_LEN)
