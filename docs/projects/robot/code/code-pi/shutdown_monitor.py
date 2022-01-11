# monitor shutdown button (GPIO13)
# sudo halt & turn off power when pressed

from gpiozero import Button
import sys, time
sys.path.append('/home/pi/iot49/projects/robot/code-pi')
import stm32

def shut_down_pi():
    # shut down and power off pi
    stm32.power_off()

with Button(13, pull_up=True, bounce_time=0.1) as shut_dn:
    shut_dn.when_pressed = shut_down_pi 
    # do this forever
    while True:
        time.sleep(600)
