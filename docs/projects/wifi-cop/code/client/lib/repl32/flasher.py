from .adafruit_miniesptool import miniesptool
from digitalio import DigitalInOut, Direction
import board, busio, time

argon_config = { \
    'rx': board.ESP_TX,
    'tx': board.ESP_RX,
    'io0': board.ESP_BOOT_MODE,
    'reset': board.ESP_WIFI_EN }
    
airlift_config = { \
    'rx': board.RX,
    'tx': board.TX,
    'io0': board.D10,
    'reset': board.D12 }


class Flasher:
    
    def __init__(self, config=argon_config):
        self.config = config
        
    def __enter__(self):
        config = self.config
        self.uart = busio.UART(tx=config['tx'], rx=config['rx'], baudrate=115200, timeout=1)
        self.resetpin = DigitalInOut(config['reset'])
        self.gpio0pin = DigitalInOut(config['io0'])
        esptool = miniesptool(self.uart, self.gpio0pin, self.resetpin, flashsize=4*1024*1024)
        esptool.debug = False
        esptool.debug_check_command = False

        esptool.sync()
        if esptool.chip_name != "ESP32":
            raise RuntimeError("Expected ESP32, got {}".format(esptool.chip_name))
        esptool.baudrate = baudrate
        print("MAC ADDR:", ":".join("{:02x}".format(x) for x in esptool.mac_addr))
        self.esptool = esptool
        return self
    
    def __exit__(self):
        self.uart.deinit()
        self.resetpin.deinit()
        self.gpio0pin.deinit()
        esptool.reset()
        time.sleep(0.5)
        
    def flash_file(self, firmware, md5sum, dry_run=False):
        self.esptool.flash_file(firmware, 0x1000, md5=md5, dry_run=dry_run)

    def erase(self, dry_run=False):
        meg = 1024*1024
        for sector in range(4):
            esptool.erase(size=meg, offset=sector*meg)
            print()
