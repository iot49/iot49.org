from array import array

try:
    const(0)
except NameError:
    # only on rpi
    def const(x): return x
    STATE_K      = const(0)    # normalized time
    STATE_PITCH  = const(1)    # pitch angle [degree]
    STATE_CPT1   = const(2)    # encoder1 counts, reset every 100th cycle
    STATE_CPT2   = const(3)    # encoder2 counts, reset every 100th cycle
    STATE_DUTY1  = const(4)    # motor1 duty cycle, +/- 100
    STATE_DUTY2  = const(5)    # motor2 duty cycle, +/- 100
    STATE_DT1    = const(6)    # controller exec time [us]
    STATE_DT2    = const(7)    # controller + state comm of _last_ cycle time [us]


#################################################################################
# commands

CMD_STATE        = const(0)    # prefix state sent by controller in every iteration
CMD_GET          = const(1)    # get parameter value
CMD_SET          = const(2)    # set parameter value
CMD_START        = const(3)    # start controller
CMD_SHUTDOWN     = const(4)    # shutdown controller
CMD_PING         = const(5)    # ping (testing)
CMD_ECHO         = const(6)    # echo (testing)


#################################################################################
# parameters

PARAM_FS         = const(0)    # controller freq [Hz], set before starting controller
PARAM_PWM        = const(1)    # motor pwm freq [Hz],  set before starting controller

PARAM_RESERVED   = const(2)    # number of reserved parameter slots 

# allocate

_PARAM_SZ         = 10         # allocate sufficient space for controllers
PARAM = array('f', [0]*_PARAM_SZ)

# defaults

PARAM[PARAM_FS]  =      100
PARAM[PARAM_PWM] =   10_000
