import paho.mqtt.client as mqtt
import json
import os
from config import *

class PlotProxy:
    
    def __init__(self, app_name, module_name, class_name, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs["title"] = app_name
        self._app_name = app_name
        client = self._mqttc = mqtt.Client(client_id="", clean_session=True, protocol=mqtt.MQTTv311)
        client.connect("localhost", port=1883, keepalive=60)
        
        # start bokeh server
        payload = (
            app_name, module_name, class_name,
            args, kwargs
        )
        client.publish(f"{TOPIC_ROOT}/start", json.dumps(payload), qos=QOS)
        
        # url
        url = f"https://{os.path.expandvars('$DNS_NAME')}.local/plotserver/{app_name}"
        print(f"serving app at {url}")
        
    def shutdown(self):
        self._mqttc.publish(f"{TOPIC_ROOT}/shutdown", json.dumps(self._app_name), qos=QOS)
        # Alternatively:
        # import urllib.request

    
# urllib.request.urlopen(f"https://{os.path.expandvars('$DNS_NAME')}.local/plotserver/{self.app_name}/shutdown")
