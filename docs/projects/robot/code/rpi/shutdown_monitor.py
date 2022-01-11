#!/usr/bin/env python

# monitor shutdown button (GPIO13)
# sudo halt & turn off power when pressed

from iot_device.pydevice import Pydevice
from gpiozero import Button
from serial import Serial
import os, requests, time


# sudo shutdown (supervisor call)
def shutdown():
    supervisor_ip = os.getenv("BALENA_SUPERVISOR_ADDRESS")
    api_key = os.getenv("BALENA_SUPERVISOR_API_KEY")
    url = f"{supervisor_ip}/v1/shutdown?apikey={api_key}"
    headers = { 'Content-Type': 'application/json' }
    requests.post(url=url, headers=headers)

    
# run code on stm32
def exec_no_follow(cmd, dev='/dev/ttyAMA1'):
    with Serial(dev, 115200, timeout=0.5, write_timeout=2, exclusive= True) as serial:
        pyd = Pydevice(serial)
        pyd.enter_raw_repl()
        pyd.exec_raw_no_follow(cmd)
        time.sleep(0.2)
        while serial.in_waiting:
            data = serial.read(serial.in_waiting)
            try:
                data = data.decode()
            except:
                pass
            print(f"*** MCU: {data}")
            time.sleep(0.1)

            
# monitor pi poweroff pin (AUX=GPIO16) and cut 5V supply when low
def stm32_shutdown_monitor():
    exec_no_follow(
f"""
from pyb import Pin
from time import sleep

# wait for pi to signal it's down
power_off = Pin('AUX', mode=Pin.IN, pull=Pin.PULL_NONE)
while power_off.value() == 1:
    pass

# just for good measure
sleep(1)

# declaring as input first sets the initial value after configuring as output
shut_dn = Pin('PWR_EN', mode=Pin.IN, pull=Pin.PULL_UP)
shut_dn.value(1)
shut_dn = Pin('PWR_EN', mode=Pin.OUT_OD)
shut_dn.value(0)

# power is cut - we are dead!
""")
    

# callback when shutdown button pressed
def shut_down_pi():
    stm32_shutdown_monitor()
    shutdown()
    

# wait for MOTOR_HAT power button press (GPIO13) to initiate shutdown
with Button(13, pull_up=True, bounce_time=0.1) as shut_dn:
    shut_dn.when_pressed = shut_down_pi 
    # do this forever
    while True:
        # print("napping ...")
        time.sleep(60)
            
