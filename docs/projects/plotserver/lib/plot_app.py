from config import *
from abc import ABC, abstractmethod
import paho.mqtt.client as mqtt
import json

class PlotApp(ABC):
    
    @abstractmethod
    def app(self, doc):
        """Implement in derived class."""
        pass
    
    def loop(self):
        self._mqttc.loop(timeout=0)
    
    @property
    def app_name(self):
        return self._app_name
    
    def __init__(self, app_name):
        self._app_name = app_name
        client = self._mqttc = mqtt.Client(client_id="", clean_session=True, protocol=mqtt.MQTTv311)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.message_callback_add(f"{TOPIC_ROOT}/call/{self.app_name}", self._on_call)
        client.connect("mosquitto", port=1883, keepalive=60)
        self.loop()
        
    def _on_call(self, client, userdata, message):
        method_name, args, kwargs = json.loads(message.payload)
        do = 'do_' + method_name        
        if hasattr(self, do) and callable(func := getattr(self, do)):
            func(*args, **kwargs)
        else:
            raise ValueError(f"***** app '{self.app_name}' has no method {do}")

    def _on_connect(self, client, userdata, flags, rc):
        self._mqttc.subscribe(f"{TOPIC_ROOT}/call/{self.app_name}", qos=QOS)

    def _on_disconnect(self, client, userdata, rc):
        print("disconnected!")
        if rc != 0: print("Network error")
