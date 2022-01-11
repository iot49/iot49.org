from iot_device.pydevice import Pydevice
from iot_device import DeviceRegistry, RemoteError
from serial import Serial
from gpiozero import LED as Pin
import asyncio, subprocess, os, time


def hard_reset(boot_mode=False):
    with Pin(21) as nrst, Pin(27) as boot0:
        if boot_mode:
            boot0.on()
        else:
            boot0.off()
        time.sleep(0.1)
        nrst.off()
        time.sleep(0.1)
        nrst.on()
        # let boot process finish
        time.sleep(1)
        
def exec(cmd, data_consumer=None, dev='serial:///dev/ttyAMA1'):    
    registry = DeviceRegistry()
    registry.register(dev)
    with registry.get_device(dev) as repl:
        res = repl.exec(cmd, data_consumer)
        try:
            res = res.decode()
        except:
            pass
        return res
    
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

def rsync(dry_run=True, dev='serial:///dev/ttyAMA1'):
    registry = DeviceRegistry()
    registry.register(dev)
    with registry.get_device(dev) as repl:
        repl.rsync(data_consumer=lambda x: print(x, end=''), dry_run=dry_run)

def rlist(dev='serial:///dev/ttyAMA1'):
    registry = DeviceRegistry()
    registry.register(dev)
    with registry.get_device(dev) as repl:
        repl.rlist(data_consumer=lambda x: print(x, end=''), show=True)

def supply_voltage():
    return float(exec(
"""
from pyb import ADC

adc = pyb.ADC('V12_DIV')
print(0.00655233*adc.read())
"""))

def flash_bin(address='0x08000000', firmware='firmware0.bin', dev='/dev/ttyAMA2', info_only=False):
    hard_reset(boot_mode=True) 
    if info_only:
        cmd = ['stm32flash', dev]
    else:
        cmd = ['stm32flash', '-v', '-S', address, '-w', firmware, dev]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout.decode())
    if len(stderr) > 0:
        print(f"***** {stderr.decode()}")

def flash():
    # flash new binaries
    # Debug: flash_bin(info_only=True)
    flash_bin(address='0x08000000', firmware='/home/pi/micropython/ports/stm32/build-MOTOR_HAT/firmware0.bin')
    flash_bin(address='0x08020000', firmware='/home/pi/micropython/ports/stm32/build-MOTOR_HAT/firmware1.bin')
    
def _power_off(delay=10):
    # turn 5V power off in delay seconds
    # call 'sudo halt' on pi immediately after running this!
    exec_no_follow(
f"""
from pyb import Pin
from time import sleep

# declaring as input first sets the initial value after configuring as output
shut_dn = Pin('PWR_EN', mode=Pin.IN, pull=Pin.PULL_UP)
shut_dn.value(1)
shut_dn = Pin('PWR_EN', mode=Pin.OUT_OD)
sleep({delay})
shut_dn.value(0)
""")
    
def power_off(delay=10):
    print(f"shutting down ...")
    _power_off(delay)
    os.system("sudo halt")

async def async_repl(cmd, dev='/dev/ttyAMA1'):
    with Serial(dev, 115200, timeout=0.5, write_timeout=2, exclusive=False) as serial:
        pyd = Pydevice(serial)
        pyd.enter_raw_repl()
        pyd.exec_raw_no_follow(cmd)
        while True:
            if serial.in_waiting:
                data = serial.read(serial.in_waiting)
                try:
                    data = data.decode()
                except:
                    pass
                print(f"MCU: {data}")
            else:
                await asyncio.sleep(0.9)

