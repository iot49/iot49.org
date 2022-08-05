#!/usr/bin/env python

# monitor shutdown button (GPIO13)
# sudo halt & turn off power when pressed

from iot_device.pydevice import Pydevice
from gpiozero import Button
from gpiozero import LED as Pin
from serial import Serial
from time import sleep
import os, requests


# sudo shutdown (supervisor call)
def shutdown():
    supervisor_ip = os.getenv("BALENA_SUPERVISOR_ADDRESS")
    api_key = os.getenv("BALENA_SUPERVISOR_API_KEY")
    url = f"{supervisor_ip}/v1/shutdown?apikey={api_key}"
    headers = { 'Content-Type': 'application/json' }
    requests.post(url=url, headers=headers)

    
# run code on stm32
def exec_no_follow(cmd, dev='/dev/ttyAMA1'):
    with Serial(dev, 115200, timeout=0.5, write_timeout=2, exclusive=False) as serial:
        pyd = Pydevice(serial)
        pyd.enter_raw_repl()
        pyd.exec_raw_no_follow(cmd)
        sleep(0.2)
        while serial.in_waiting:
            data = serial.read(serial.in_waiting)
            try:
                data = data.decode()
            except:
                pass
            print(f"*** MCU: {data}")
            sleep(0.1)

            
# monitor pi poweroff pin (AUX=GPIO16) and cut 5V supply when low
def stm32_shutdown_monitor():
    # reset STM32
    with Pin(21) as nrst, Pin(27) as boot0:
        boot0.off()
        sleep(0.1)
        nrst.off()
        sleep(0.1)
        nrst.on()
        # let boot process finish
        sleep(1)
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

# at this point power is cut - program never gets beyond
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
        sleep(60)
            
