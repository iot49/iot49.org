import micropython, machine, network, ntptime, time
import secrets

# handle errors in interrupts
micropython.alloc_emergency_exception_buf(100)

def connect():
    """connect to wifi, get ntp time, advertise hostname (if not None)"""
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected(): return True
    wlan.active(True)
    # wlan.scan()   # improves connection reliability???
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
        return False
    # set clock to local time
    tm = time.localtime(ntptime.time() + getattr(secrets, 'tz_offset', 0))
    print("time", tm)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    return True

# connect to WiFi
conneced = connect()

if connected and hasattr(secrets, 'webrepl_pwd'):
    # start webrepl
    import webrepl
    webrepl.start()

    # advertise
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
