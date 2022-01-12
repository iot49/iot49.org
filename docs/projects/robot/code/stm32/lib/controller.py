# controller.py

from pyb import Timer, Pin
from machine import I2C
from array import array
from time import ticks_us, ticks_diff, sleep_ms
from pid import PID
from encoder import init_encoder, c2
from tb6612 import TB6612
from bno055 import BNO055, NDOF_FMC_OFF_MODE, QUAT_DATA
from comm import CMD_STATE
import gc, math


# integer state

INAMES = [
    'k',        # time is k*T
    'dt1 [us]', # cpu time w/o sending state
    'dt2 [us]', # cpu time total
    'enc1',     # encoder 1 total count
    'enc2',     # encoder 2 total count
]

_ISTATE_K       = const(0)
_ISTATE_DT1     = const(1)
_ISTATE_DT2     = const(2)
_ISTATE_ENC1    = const(3)
_ISTATE_ENC2    = const(4)

# float state 
         
FNAMES = [
    'cpt1',         # encoder 1 count per period T=1/fs
    'cpt2',         # encoder 1 count per period T=1/fs
    'cpt1_sp',      # cpt1 setpoint
    'cpt2_sp',      # cpt1 setpoint
    'duty1',        # pwm duty control motor 1, +/-100
    'duty2',        # pwm duty control motor 2, +/-100
    'pitch [deg]',  # robot pitch (angle wrt vertical)
    'quat_w',       # quaternion
    'quat_x',       # quaternion
    'quat_y',       # quaternion
    'quat_z',       # quaternion
]

_FSTATE_CPT1    = const( 0)
_FSTATE_CPT2    = const( 1)
_FSTATE_CPT1_SP = const( 2)
_FSTATE_CPT2_SP = const( 3)
_FSTATE_DUTY1   = const( 4)
_FSTATE_DUTY2   = const( 5)
_FSTATE_PITCH   = const( 6)
_FSTATE_QUAT_W  = const( 7)
_FSTATE_QUAT_X  = const( 8)
_FSTATE_QUAT_Y  = const( 9)
_FSTATE_QUAT_Z  = const(10)

# pid controllers

PID_CPT1        = const(0)
PID_CPT2        = const(1)

RAD2DEG = 180/math.pi

# called by timer interrupt

class Controller:
    
    def __init__(self, uart, pwm_freq):
        self.uart = uart

        self.i_state = array('i', [0] * len(INAMES))
        self.f_state = array('f', [0] * len(FNAMES))
     
        # controller timer
        self.controller_timer = Timer(1)
        
        # motor power control
        self.nstby = Pin('NSTBY', mode=Pin.OUT_PP)
        self.nstby.value(0)
        
        # motors
        motor_pwm_timer = Timer(8, freq=pwm_freq)
        self.motor1 = TB6612(
            motor_pwm_timer.channel(3, Timer.PWM_INVERTED, pin=Pin('PWM_A')),
            Pin('AIN1', mode=Pin.OUT_PP),
            Pin('AIN2', mode=Pin.OUT_PP)
        )
        self.motor2 = TB6612(
            motor_pwm_timer.channel(1, Timer.PWM_INVERTED, pin=Pin('PWM_B')),
            Pin('BIN1', mode=Pin.OUT_PP),
            Pin('BIN2', mode=Pin.OUT_PP)
        )
       
        # encoders
        self.enc1 = init_encoder(4, 'ENC_A1', 'ENC_A2', Pin.AF2_TIM4)
        self.enc2 = init_encoder(3, 'ENC_B1', 'ENC_B2', Pin.AF2_TIM3)
        
        # gyro
        i2c = I2C(1, freq=400_000)
        imu = BNO055(i2c, crystal=True, transpose=(2, 0, 1), sign=(0, 0, 1))
        imu.mode(NDOF_FMC_OFF_MODE)
        sleep_ms(800)
        imu.iget(QUAT_DATA)
        self.imu = imu
        
        # pid controllers
        self.pid = [
            PID(1, 7, 50, 0, -100, 100),
            PID(1, 7, 50, 0, -100, 100),
        ]
        
    def start(self, fs, controller_name="duty_control"):
        self.stop()
        self.control_laws = getattr(self, controller_name)
        self.set_fs(fs)
        self.nstby.value(1)
        gc.collect()
        self.controller_timer.init(freq=fs, callback=self.control)
        
    def stop(self):
        self.controller_timer.callback(None)                
        self.nstby.value(0)
        
    def shutdown(self):
        self.controller_timer.deinit()             
        self.nstby.value(0)
        
    def set_fs(self, fs):
        for pid in self.pid:
            pid.Ts = 1/fs
    
    def set_kp(self, pid_index, kp):
        self.pid[pid_index].kp = kp
        
    def set_ki(self, pid_index, ki):
        self.pid[pid_index].ki = ki
        
    def set_kd(self, pid_index, kd):
        self.pid[pid_index].kd = kd
        
    def control(self, timer):
        start_us = ticks_us()

        # locals
        i_state = self.i_state
        f_state = self.f_state

        # time index
        i_state[_ISTATE_K] += 1

        # encoders
        enc1 = self.enc1
        enc2 = self.enc2
        cps1 = -c2(enc1.counter())
        enc1.counter(0)
        cps2 = c2(enc2.counter())
        enc2.counter(0)
        i_state[_ISTATE_ENC1] += cps1
        i_state[_ISTATE_ENC2] += cps2
        f_state[_FSTATE_CPT1] = cps1
        f_state[_FSTATE_CPT2] = cps2
        
        # gyro
        imu = self.imu
        imu.iget(QUAT_DATA)
        f_state[_FSTATE_QUAT_W] = w = imu.w/(1<<14)
        f_state[_FSTATE_QUAT_X] = x = imu.x/(1<<14)
        f_state[_FSTATE_QUAT_Y] = y = imu.y/(1<<14)
        f_state[_FSTATE_QUAT_Z] = z = imu.z/(1<<14)
        sinp = 2 * (w * y - z * x);
        if abs(sinp) >= 1:
            # use 90 degrees if out of range
            pitch = math.copysign(math.pi / 2, sinp);
        else:
            pitch = math.asin(sinp)
        pitch *= RAD2DEG
        f_state[_FSTATE_PITCH] = pitch
        
        # call control code
        self.control_laws()
        
        # controller execution time
        i_state[_ISTATE_DT1] = ticks_diff(ticks_us(), start_us)

        # status
        uart = self.uart
        uart.writechar(CMD_STATE)
        uart.write(i_state)
        uart.write(f_state)
        
        # total execution time
        i_state[_ISTATE_DT2] = ticks_diff(ticks_us(), start_us)
        

    def duty_control(self):
        f_state = self.f_state
        self.motor1.speed(f_state[_FSTATE_DUTY1])
        self.motor2.speed(f_state[_FSTATE_DUTY2])

        
    def speed_control(self):
        f_state = self.f_state
        pid = self.pid
        cps1 = f_state[_FSTATE_CPT1]
        cps2 = f_state[_FSTATE_CPT2]

        # control
        pid[PID_CPT1].setpoint = f_state[_FSTATE_CPT1_SP]
        pid[PID_CPT2].setpoint = f_state[_FSTATE_CPT2_SP]
        duty1 = pid[PID_CPT1].update(cps1)
        duty2 = pid[PID_CPT2].update(cps2)
        self.motor1.speed(duty1)
        self.motor2.speed(duty2)
        f_state[_FSTATE_DUTY1] = duty1
        f_state[_FSTATE_DUTY2] = duty2
