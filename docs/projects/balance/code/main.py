import ble_uart_peripheral
import bluetooth

# from scale import Scale
from scale_hx711 import ScaleHX711 as Scale

from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from button import Button

# configure the Bluetooth UART
ble = bluetooth.BLE()
uart = ble_uart_peripheral.BLEUART(ble)

# Scale & Display
i2c = I2C(0, scl=Pin(22), sda=Pin(23))

oled_width = 128
oled_height = 32
oled = SSD1306_I2C(oled_width, oled_height, i2c)

scale = Scale()
tare_button = Button(15, scale.tare)

last_weight = 500
while True:
    weight = scale.measure()
    if abs(weight-last_weight) > 3:
        # send via Bluetooth
        uart.write("{:8.1f} gram\n".format(weight))
        # show on display
        oled.fill(0)
        oled.text("{:8.1f} gram".format(weight), 0, 12)
        oled.show()
        last_weight = weight
