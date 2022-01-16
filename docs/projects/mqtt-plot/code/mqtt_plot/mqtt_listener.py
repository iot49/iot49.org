from . config import *
from numpy import array
from struct import unpack
import paho.mqtt.client as mqtt
import json


class MqttListener:
    
    def __init__(self, app):
        self._app = app
        # mqtt client
        client = self._client = mqtt.Client(clean_session=True, protocol=mqtt.MQTTv311)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/new", self._on_new)
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/add", self._on_add)
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/bin", self._on_bin)
        client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        # background task listening for messages
        client.loop_start()

    @property
    def column_names(self):
        return self._app.column_names
    
    def _on_new(self, client, _,  message):
        data = json.loads(message.payload)
        # data source
        cols = data.get("columns", [])
        if not isinstance(cols, list):
            return
        # properties
        rollover = 500
        try:
            rollover = int(data.get("rollover"))
        except (ValueError, TypeError):
            pass
        args = data.get("args", {})
        args = args if isinstance(args, dict) else {}
        spec = data.get("layout", "line_plot")
        # update the app
        self._app.update_appearance(spec, cols, args, rollover)

    def _on_add(self, client, _,  message):
        row = json.loads(message.payload)
        # numpy array for nan to work
        df = { c:array([row.get(c, float('nan'))]) for c in self.column_names }
        self._app.add_data(df)

    def _on_bin(self, client, _,  message):
        row = list(unpack(f"!{len(message.payload)//4}f", message.payload))
        # pad in case we received too few floats
        cn = self.column_names
        diff = len(cn) - len(row)
        if diff > 0: row.extend([array(float('nan'))]*diff)
        df = { c:array([row[i]]) for i,c in enumerate(cn) }
        self._app.add_data(df)
        
    def _on_connect(self, client, _, flags, rc):
        self._client.subscribe(f"{MQTT_TOPIC_ROOT}/#", qos=MQTT_QOS)

    def _on_disconnect(self, _1, _2, rc):
        print("disconnected!")
        if rc != 0: print("Network error")
