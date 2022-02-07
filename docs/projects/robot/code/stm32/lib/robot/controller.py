# controller.py

from . state import STATE, EXEC_T, FS, PWM_FREQ, CMD_STATE
from encoder16 import Encoder16
from tb6612 import TB6612
from bno055 import BNO055, NDOF_FMC_OFF_MODE, QUAT_DATA
from pyb import Timer, Pin
from machine import I2C
from array import array
from time import ticks_us, ticks_diff, sleep_ms
import gc, math

# allocate emergency exception buffer
import micropython
micropython.alloc_emergency_exception_buf(100)

# state
_K                 = const( 0)    # normalized time, t = K/FS
_PITCH             = const( 1)    # pitch angle [degree]
_ODO_1             = const( 2)    # encoder 1 sum
_ODO_2             = const( 3)    # encoder 2 sum
_TACHO_CM          = const( 4)    # derivative of 0.5 * (ODO_1 + ODO_2)
_TACHO_DIFF        = const( 5)    # derivative of of ODO_1 - ODO_2
_DUTY_CM           = const( 6)    # mean of motor duty cycle, +/- 100
_DUTY_DIFF         = const( 7)    # difference of motor duty cycles, +/- 200
_EXEC_T            = const( 8)    # controller irq exec time [us]
_STATE_LEN         = const(_EXEC_T + 1)

# send status to host
_CMD_STATE = const(0)

# gyro pitch helpers
_RAD2DEG = 180/math.pi
_90DEG = 0.5 * math.pi
_QUAT_SCALE = 1/(2<<26)

# checks
assert _CMD_STATE == CMD_STATE, f"cmd_state: {_CMD_STATE} != {CMD_STATE}"
assert _EXEC_T == EXEC_T


class Controller:
    
    def __init__(self, uart):
        self.uart = uart

        # state, sent to host in every iteration
        self.state = memoryview(STATE)[_K:_STATE_LEN]
     
        # motors
        pwm_timer = Timer(8, freq=int(STATE[PWM_FREQ]))
        scale = (pwm_timer.period()+1)/100
        self.motor1 = TB6612(
            pwm_timer.channel(3, Timer.PWM_INVERTED, pin=Pin('PWM_A')),
            scale,
            Pin('AIN1', mode=Pin.OUT_PP),
            Pin('AIN2', mode=Pin.OUT_PP)
        )
        self.motor2 = TB6612(
            pwm_timer.channel(1, Timer.PWM_INVERTED, pin=Pin('PWM_B')),
            scale,
            Pin('BIN1', mode=Pin.OUT_PP),
            Pin('BIN2', mode=Pin.OUT_PP)
        )
       
        # encoders
        self.enc1 = Encoder16(4, 'ENC_A1', 'ENC_A2', Pin.AF2_TIM4)
        self.enc2 = Encoder16(3, 'ENC_B1', 'ENC_B2', Pin.AF2_TIM3)
        
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
        self._ctrl_timer.init(freq=int(STATE[FS]), callback=self._handler)

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
        state[_K] += 1

        # encoders
        odo1  =  self.enc1.count()
        odo2  = -self.enc2.count()
        tach1 = state[_ODO_1] - odo1
        tach2 = state[_ODO_2] - odo2
        state[_ODO_1]      = odo1
        state[_ODO_2]      = odo2
        state[_TACHO_CM]   = 0.5 * (tach1 + tach2)
        state[_TACHO_DIFF] = tach1 - tach2

        # gyro
        imu = self.imu
        imu.iget(QUAT_DATA)
        sinp = _QUAT_SCALE * (imu.w * imu.y - imu.z * imu.x)
        if abs(sinp) >= 1:
            # use 90 degrees if out of range
            pitch = math.copysign(_90DEG, sinp)
        else:
            pitch = math.asin(sinp)
        state[_PITCH] = _RAD2DEG * pitch
        
        # call control code
        self.update()
        
        # motor speed
        self.motor1.speed(state[_DUTY_CM] + 0.5*state[_DUTY_DIFF])
        self.motor2.speed(state[_DUTY_CM] - 0.5*state[_DUTY_DIFF])
        
        # send status to host
        uart = self.uart
        uart.writechar(_CMD_STATE)
        uart.writechar(_STATE_LEN)
        uart.write(state)
        
        # total execution time
        state[_EXEC_T] = ticks_diff(ticks_us(), start_us)
