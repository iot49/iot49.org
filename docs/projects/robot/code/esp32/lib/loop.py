from remote import BLE_UART, JoyAxis, Button, Encoder
from machine import ADC, Pin, deepsleep, reset_cause, PWRON_RESET
from struct import pack, unpack
from time import ticks_ms, ticks_diff, sleep_ms
import esp32

"""
Messages: 
--------

Format: 
pack('>Bf', ord(code), value)

Codes:

a) MCU -> Pi
   x, y: joystick position
   q, b, c: button pressed counts 
         Note: button 1 assigned to 'q' (quit = deepsleep)
   1, 2, 2: encoder counts
   v: v_bat [V]
   h: heartbeat count
   
b) Pi -> MCU
   R, G, B: led on/off (1/0)
   Q: power down remote (deepsleep)
"""

HARTBEAT_MS =  1000     # frequency with which hartbeats are sent [ms]
SHUTDOWN_MS = 60000     # shut down if no connection in specified time [ms]
VBATT_MS    = 60000     # rate at which battery level is sent [ms]

def loop():
    
    # deepsleep wakeup
    deepsleep_wakeup_pin = Pin(4, mode=Pin.IN, pull=Pin.PULL_UP)
    esp32.wake_on_ext0(deepsleep_wakeup_pin, esp32.WAKEUP_ALL_LOW)

    # BLE
    def rx_cb(data):
        nonlocal red, green, blue
        code, value = unpack('>Bf', data)
        code = chr(code)
        # print("ESP32: recv", code, value)
        value = value > 0
        if code == 'R': red.value(value)
        if code == 'G': green.value(value)
        if code == 'B': blue.value(value)
        if code == 'Q':
            print("deepsleep requested by central")
            deepsleep() 
        
    uart = BLE_UART(rx_cb=rx_cb)
    
    def send(code: char, value: float):
        # print("ESP32: send", code, value)
        uart.send(pack('>Bf', ord(code), value))
        
    # Hartbeat
    last_hartbeat = ticks_ms()
    hartbeat_count = 0
        
    # Joystick
    joy_x = JoyAxis(34)
    joy_y = JoyAxis(36)
        
    # Push buttons    
    button_1 = Button(deepsleep_wakeup_pin)
    button_2 = Button(Pin(25, mode=Pin.IN, pull=Pin.PULL_UP))
    button_3 = Button(Pin(26, mode=Pin.IN, pull=Pin.PULL_UP))

    # Encoders
    enc1 = Encoder(Pin(32, mode=Pin.IN, pull=Pin.PULL_UP), Pin(14, mode=Pin.IN, pull=Pin.PULL_UP))
    enc2 = Encoder(Pin(33, mode=Pin.IN, pull=Pin.PULL_UP), Pin(15, mode=Pin.IN, pull=Pin.PULL_UP))
    enc3 = Encoder(Pin(12, mode=Pin.IN, pull=Pin.PULL_UP), Pin(27, mode=Pin.IN, pull=Pin.PULL_UP))
    enc1_last = enc1.count
    enc2_last = enc2.count
    enc3_last = enc3.count
    
    # LEDs
    red   = Pin(17, mode=Pin.OUT)
    green = Pin(16, mode=Pin.OUT)
    blue  = Pin(19, mode=Pin.OUT)
    power_led = red
    power_led.value(1)
    connected_led = green
    
    # LiPo battery voltage
    v_bat_adc = ADC(Pin(35))
    v_bat_adc.atten(ADC.ATTN_11DB)
    v_bat_last_xmit = ticks_ms() - VBATT_MS + 3000
    
    # start powered-down
    if reset_cause() == PWRON_RESET:
        deepsleep()
    
    # Forever loop (until power off)
    while True:
        start = ticks_ms()

        # connected?
        if not uart.is_connected():
            connected_led.value(0)
            while not uart.is_connected() and \
                    ticks_diff(ticks_ms(), start) < 60_000 and \
                    not button_1.pressed:
                sleep_ms(100)
            if not uart.is_connected() or button_1.pressed:
                while deepsleep_wakeup_pin.value() == 0:
                    pass
                print("deepsleep timeout")
                deepsleep()
            # reset encoder counts and start loop
            enc1.reset()
            enc2.reset()
            enc3.reset()
        connected_led.value(1)
        
        # Joystick
        x = joy_x.read_changed()
        if x: send('x', -x)
        y = joy_y.read_changed()
        if y: send('y',  y)

        # Buttons
        if button_1.pressed: 
            # power down remote
            send('q', button_1.count)
            # wait for user to release button (otherwise it will start right away)
            while deepsleep_wakeup_pin.value() == 0:
                pass
            print("deepsleep power button")
            deepsleep()
        if button_2.pressed: 
            send('b', button_2.count)
        if button_3.pressed: 
            send('c', button_3.count)

        # Encoders
        if enc1.count != enc1_last:
            enc1_last = enc1.count
            send('1', enc1_last)
        if enc2.count != enc2_last:
            enc2_last = enc2.count
            send('2', enc2_last)
        if enc3.count != enc3_last:
            enc3_last = enc3.count
            send('3', enc3_last)
            
        # v_bat
        if ticks_diff(start, v_bat_last_xmit) > VBATT_MS:
            send('v', v_bat_adc.read()*4.178/2463)
            v_bat_last_xmit = start
            
        # heartbeat
        if ticks_diff(start, last_hartbeat) > HARTBEAT_MS-50:
            hartbeat_count += 1
            last_hartbeat = start
            send('h', hartbeat_count)
                       
        sleep_ms(50)
