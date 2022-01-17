from array import array

try:
    const(0)
except NameError:
    def const(x): return x


# parameters: controllers may define additional parameters (e.g. setpoints)

PARAM_FS         = const(0)      # controller freq [Hz], set before starting controller
PARAM_PWM        = const(1)      # motor pwm freq [Hz],  set before starting controller

# allocate

PARAM_SZ         = 10            # allocate sufficient space for controllers
PARAM = array('f', [0]*PARAM_SZ)

# defaults

PARAM[PARAM_FS]  =      100
PARAM[PARAM_PWM] =   10_000


# commands

CMD_STATE        = const(0)      # prefix state sent by controller in every iteration
CMD_GET          = const(1)      # get parameter value
CMD_SET          = const(2)      # set parameter value
CMD_START        = const(3)      # start controller
CMD_SHUTDOWN     = const(4)      # shutdown controller
CMD_PING         = const(5)      # ping (testing)
CMD_ECHO         = const(6)      # echo (testing)
