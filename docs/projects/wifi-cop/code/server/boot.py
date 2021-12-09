import micropython, machine, network, ntptime, gc, time
import secrets


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
    for _ in range(50):
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
Partition.mark_app_valid_cancel_rollback()

# connect to WiFi
connect()

if False:
    # start & advertise webrepl
    import webrepl
    webrepl.start()

    from socket import socket, AF_INET, SOCK_DGRAM
    import _thread

    def broadcaster(msg, port):
        so = socket(AF_INET, SOCK_DGRAM)
        try:
            # pre-allocate address (on heap)
            addr = ('255.255.255.255', port)
            while True:
                so.sendto(msg, addr)
                time.sleep(1)
        finally:
            so.close()

    msg = "ws://{}:8266\n{}".format(
        network.WLAN(network.STA_IF).ifconfig()[0],
        ":".join("{:02x}".format(x) for x in machine.unique_id())
    )
    th = _thread.start_new_thread(broadcaster, (msg, getattr(secrets, 'broadcast_port', 50000)))

# cleanup
gc.collect()

