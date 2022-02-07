# fix wiring issue
import os
if os.getenv('BALENA_DEVICE_ARCH') == 'aarch64':
    from gpiozero import Button as Pin
    Pin(14, pull_up=False)
    
from . abstract_robot import AbstractRobot
from . remote import Remote
