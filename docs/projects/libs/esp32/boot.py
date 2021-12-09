import micropython, machine, network, ntptime, gc, time
import secrets

micropython.alloc_emergency_exception_buf(100)

def connected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.isconnected()

def ip_addr():
    wlan = network.WLAN(network.STA_IF)
    return wlan.ifconfig()[0]

def connect(mdns_name=None):
    """connect to wifi, get ntp time, advertise hostname (if not None)"""
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected(): return
    wlan.active(True)
    if not mdns_name:
        uid = machine.unique_id()
        mdns_name = "esp32_" + "".join("{:02x}".format(x) for x in uid)
    # known on net as mdns_name.local
    wlan.config(dhcp_hostname=mdns_name)
    print("Connecting to WLAN ... ", end="")
    wlan.connect(getattr(secrets, 'wifi_ssid', 'SSID'),
                 getattr(secrets, 'wifi_pwd', ''))
    # wait for connection to be established ...
    for _ in range(30):
        if wlan.isconnected(): break
        time.sleep_ms(100)
    if not wlan.isconnected():
        print("Unable to connect to WiFi!")
        wlan.disconnect()
        return
    print("IP", wlan.ifconfig()[0])
    print("mDNS", mdns_name + ".local")
    # set clock to local time
    tm = time.localtime(ntptime.time() + getattr(secrets, 'tz_offset', 0))
    print("time", tm)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


# OTA ... accept uploaded image (if we uploaded a new one)
from esp32 import Partition
try:
    Partition.mark_app_valid_cancel_rollback()
except OSError:
    pass

# connect to WiFi
connect()

if True:
    # webrepl
    import webrepl
    webrepl.start()
    try:
        network.WLAN(network.STA_IF).mdns_add_service('_ws', '_tcp', 8266)
    except AttributeError:
        pass

gc.collect()