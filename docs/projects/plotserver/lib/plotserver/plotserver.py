from .httpd_server import HttpdServer
from .mqtt_server import MqttServer
from .app_dict import AppDict

import os, sys, threading

sys.path.append(os.path.expanduser('~/plotserver/lib'))
from config import *

def serve():
    port_range = set(range(5000, 5010, 1))
    app_dict = AppDict(port_range)
    mqttc = MqttServer(app_dict)
    th = threading.Thread(name="mqtt", target=mqttc.loop_forever, daemon=True)
    th.start()
    
    httpd = HttpdServer(app_dict)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("shutdown ...")
        httpd.shutdown()
        httpd.server_close()
        
serve()