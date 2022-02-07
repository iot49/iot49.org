from array import array
from . import pid

try:
    _ = const(0)
except NameError:
    def const(x): return x


# commands

CMD_STATE         = const( 0)    # prefix state sent by controller in every iteration
CMD_GET_ALL       = const( 1)    # get STATE array
CMD_GET           = const( 2)    # get STATE[i]
CMD_SET           = const( 3)    # set STATE[i]
CMD_START         = const( 4)    # start controller
CMD_SHUTDOWN      = const( 5)    # shutdown controller
CMD_PING          = const( 6)    # ping (testing)
CMD_ECHO          = const( 7)    # echo (testing)


# controller state and parameters
# copies on stm32 and rpi kept in sync

_STATE_LEN        = const(30)
_PID_STATE_LEN    = const( 8)

STATE = array('f', [0]*_STATE_LEN)


# controller state - sent to rpi by irq handler

K                 = const( 0)    # normalized time, t = K/FS
PITCH             = const( 1)    # pitch angle [degree]
ODO_1             = const( 2)    # encoder 1 sum
ODO_2             = const( 3)    # encoder 2 sum
TACHO_CM          = const( 4)    # derivative of 0.5 * (ODO_1 + ODO_2)
TACHO_DIFF        = const( 5)    # derivative of of ODO_1 - ODO_2
DUTY_CM           = const( 6)    # mean of motor duty cycle, +/- 100
DUTY_DIFF         = const( 7)    # difference of motor duty cycles, +/- 200
EXEC_T            = const( 8)    # controller irq exec time [us]

# parameters
# IMPORTANT: set FS before setting PID controller parameters
#            set FS, PWM_FREQ before 

FS                = const( 9)    # controller irq rate
PWM_FREQ          = const(10)    # motor pwm freq
DUTY_DEAD         = const(11)    # one-sided motor deadzone
SET_DUTY_CM       = const(12)    # target speed
SET_DUTY_DIFF     = const(13)    # target delta speed

STATE[FS]         =    100       # default
STATE[PWM_FREQ]   = 10_000
STATE[DUTY_DEAD]  =      8

# pid controller states

PID_TACH_CM       = const(SET_DUTY_DIFF+1)
PID_TACH_DIFF     = const(PID_TACH_CM + _PID_STATE_LEN)

# checks

_STATE_LEN_CHECK = PID_TACH_DIFF + _PID_STATE_LEN
assert _STATE_LEN == _STATE_LEN_CHECK, f"state.py _STATE_LEN: {_STATE_LEN} != {_STATE_LEN_CHECK}"
assert _PID_STATE_LEN == pid.STATE_LEN, f"state.py _PID_STATE_LEN: {_PID_STATE_LEN} != {pid.STATE_LEN}"
