# controller.py

from param import PARAM, PARAM_FS, PARAM_PWM, CMD_STATE
from pyb import Timer, Pin
from machine import I2C
from array import array
from time import ticks_us, ticks_diff, sleep_ms
from encoder import init_encoder, c2
from tb6612 import TB6612
from bno055 import BNO055, NDOF_FMC_OFF_MODE, QUAT_DATA
import gc, math

# allocate emergency exception buffer
import micropython
micropython.alloc_emergency_exception_buf(100)

# state
STATE_K      = const(0)    # normalized time
STATE_PITCH  = const(1)    # pitch angle [degree]
STATE_CPT1   = const(2)    # encoder1 counts in last cycle
STATE_CPT2   = const(3)    # encoder1 counts in last cycle
STATE_DUTY1  = const(4)    # motor1 duty cycle, +/- 100
STATE_DUTY2  = const(5)    # motor2 duty cycle, +/- 100
STATE_DT1    = const(6)    # controller exec time [us]
STATE_DT2    = const(7)    # controller + state comm of _last_ cycle time [us]

STATE_LEN    = const(8)    # lenght of state vector

# send status to host
_CMD_STATE   = const(1)

# gyro pitch helpers
_RAD2DEG = 180/math.pi
_90DEG = 0.5 * math.pi
_QUAT_SCALE = 1/(2<<26)


class Controller:
    
    def __init__(self, uart):
        self.uart = uart

        # state, sent to host in every iteration
        self.state = array('f', [0] * STATE_LEN)
     
        # motors
        pwm_timer = Timer(8, freq=int(PARAM[PARAM_PWM]))
        self.motor1 = TB6612(
            pwm_timer.channel(3, Timer.PWM_INVERTED, pin=Pin('PWM_A')),
            Pin('AIN1', mode=Pin.OUT_PP),
            Pin('AIN2', mode=Pin.OUT_PP)
        )
        self.motor2 = TB6612(
            pwm_timer.channel(1, Timer.PWM_INVERTED, pin=Pin('PWM_B')),
            Pin('BIN1', mode=Pin.OUT_PP),
            Pin('BIN2', mode=Pin.OUT_PP)
        )
       
        # encoders
        self.enc1 = init_encoder(4, 'ENC_A1', 'ENC_A2', Pin.AF2_TIM4)
        self.enc2 = init_encoder(3, 'ENC_B1', 'ENC_B2', Pin.AF2_TIM3)
        
        # gyro
        i2c = I2C(1, freq=400_000)
        self.imu = imu = BNO055(i2c, crystal=True, transpose=(2, 0, 1), sign=(0, 0, 1))
        imu.mode(NDOF_FMC_OFF_MODE)
        sleep_ms(800)
        imu.iget(QUAT_DATA)

        # motor power control
        self.nstby = Pin('NSTBY', mode=Pin.OUT_PP)
        self.nstby.value(1)

        # start the controller
        gc.collect()
        self.nstby.value(1)
        self._ctrl_timer = Timer(1)
        self._ctrl_timer.init(freq=int(PARAM[PARAM_FS]), callback=self._handler)

    def update(self):
        """Actual control code. Implement in derived class. Default does nothing."""
        pass
        
    # turn off motors, timer interrupt and release resources
    def shutdown(self):
        self.nstby.value(0)
        self._ctrl_timer.deinit()             

    # called by timer interrupt
    def _handler(self, timer):
        start_us = ticks_us()
        state = self.state

        # time index
        state[STATE_K] += 1

        # encoders
        enc1 = self.enc1
        enc2 = self.enc2
        cpt1 = -c2(enc1.counter())
        enc1.counter(0)
        cpt2 =  c2(enc2.counter())
        enc2.counter(0)
        state[STATE_CPT1] = cpt1
        state[STATE_CPT2] = cpt2

        # motor speed
        self.motor1.speed(state[STATE_DUTY1])
        self.motor2.speed(state[STATE_DUTY2])
        
        # gyro
        imu = self.imu
        imu.iget(QUAT_DATA)
        sinp = _QUAT_SCALE * (imu.w * imu.y - imu.z * imu.x)
        if abs(sinp) >= 1:
            # use 90 degrees if out of range
            pitch = math.copysign(_90DEG, sinp)
        else:
            pitch = math.asin(sinp)
        state[STATE_PITCH] = _RAD2DEG * pitch
        
        # call control code
        self.update()
        
        # controller execution time
        state[STATE_DT1] = ticks_diff(ticks_us(), start_us)

        # send status to host
        uart = self.uart
        uart.writechar(CMD_STATE)
        uart.writechar(STATE_LEN)
        uart.write(state)
        
        # total execution time
        state[STATE_DT2] = ticks_diff(ticks_us(), start_us)
