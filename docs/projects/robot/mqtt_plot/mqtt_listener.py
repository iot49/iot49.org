from . config import *
from bokeh.models import ColumnDataSource
import paho.mqtt.client as mqtt
import json, socket, queue


class MqttListener:
    
    def __init__(self):
        self._queue = None
        self._data_source = None
        self._layout = "line_plot"
        self._args = {}
        client = self._client = mqtt.Client(clean_session=True, protocol=mqtt.MQTTv311)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/new", self._on_new)
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/add", self._on_add)
        client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        # background task listening for messages
        client.loop_start()

    def update(self):
        # move data from receive queue to column_data_source
        if not self._data_source:
            return
        try:
            while not self._queue.empty():
                new_data = self._queue.get()
                df = { c: [new_data.get(c)] for c in self.column_names }
                self._data_source.stream(df, rollover=self._rollover)
        except Exception as e:
            print(f"*** MqttListener.update: {e}")
    
    @property
    def column_data_source(self):
        return self._data_source
    
    @property
    def column_names(self):
        return self._data_source.column_names if self._data_source else []
    
    @property
    def layout(self):
        return self._layout
    
    @property
    def args(self):
        return self._args
        
    def _on_new(self, client, _,  message):
        # { columns: [], rollover: 500 }
        data = json.loads(message.payload)
        self._rollover = 500
        try:
            self._rollover = int(data.get("rollover"))
        except (ValueError, TypeError):
            pass
        self._layout = data.get("layout", "line_plot")
        args = data.get("args", {})
        self._args = args if isinstance(args, dict) else {}
        # data source
        df = { trace: [] for trace in data.get("columns", {}) }
        self._data_source = ColumnDataSource(data=df)     
        self._queue = queue.Queue()

    def _on_add(self, client, _,  message):
        row = json.loads(message.payload)
        if not self._queue:
            print("columns not defined, ignoring data")
            return
        self._queue.put_nowait(row)

    def _on_connect(self, client, _, flags, rc):
        self._client.subscribe(f"{MQTT_TOPIC_ROOT}/new", qos=MQTT_QOS)
        self._client.subscribe(f"{MQTT_TOPIC_ROOT}/add", qos=MQTT_QOS)

    def _on_disconnect(self, _1, _2, rc):
        print("disconnected!")
        if rc != 0: print("Network error")
