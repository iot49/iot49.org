from . config import *
from bokeh.models import ColumnDataSource
from numpy import array
from struct import unpack
import paho.mqtt.client as mqtt
import json, socket, queue, sys, os, signal


class MqttListener:
    
    def __init__(self):
        self._queue = None
        self._data_source = None
        self._column_names = []
        self._layout = "line_plot"
        self._args = {}
        client = self._client = mqtt.Client(clean_session=True, protocol=mqtt.MQTTv311)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/new", self._on_new)
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/add", self._on_add)
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/bin", self._on_bin)
        client.message_callback_add(f"{MQTT_TOPIC_ROOT}/quit", self._on_quit)
        client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        # background task listening for messages
        client.loop_start()

    def update(self):
        # call this regularly to move data from receive queue to column_data_source
        if not self._data_source:
            return
        try:
            while not self._queue.empty():
                df = self._queue.get()
                self._data_source.stream(df, rollover=self._rollover)
        except Exception as e:
            print(f"*** MqttListener.update: {e}")
    
    @property
    def column_data_source(self):
        # bokeh.models.ColumnDataSource
        return self._data_source
    
    @property
    def column_names(self):
        return self._column_names
    
    @property
    def layout(self):
        return self._layout
    
    @property
    def args(self):
        return self._args
        
    def _on_new(self, client, _,  message):
        # { columns: [], rollover: 500 }
        data = json.loads(message.payload)
        # data source
        cols = data.get("columns", [])
        print("_on_new", cols)
        if not isinstance(cols, list):
            return
        self._column_names = cols
        self._data_source = ColumnDataSource(data={ t: [] for t in cols })     
        # properties
        self._rollover = 500
        try:
            self._rollover = int(data.get("rollover"))
        except (ValueError, TypeError):
            pass
        self._layout = data.get("layout", "line_plot")
        args = data.get("args", {})
        self._args = args if isinstance(args, dict) else {}
        self._queue = queue.Queue()

    def _on_add(self, client, _,  message):
        row = json.loads(message.payload)
        if not self._queue:
            print("add: columns not defined, ignoring data")
            return
        # numpy array to get nan to work
        df = { cn:array([row.get(cn, float('nan'))]) for cn in self._column_names }
        self._queue.put_nowait(df)

    def _on_bin(self, client, _,  message):
        if not self._queue:
            print("bin: columns not defined, ignoring data")
            return
        row = list(unpack(f"!{len(message.payload)//4}f", message.payload))
        # pad in case we received too few floats
        cn = self._column_names
        diff = len(cn) - len(row)
        if diff > 0: row.extend([array(float('nan'))]*diff)
        df = { c: array([row[i]]) for i,c in enumerate(cn) }
        self._queue.put_nowait(df)
        
    def _on_quit(self, _1, _2, _3):
        print("quit")
        self._client.disconnect()
        # rudely kill tornado (is there a better solution?)
        os.kill(os.getpid(), signal.SIGUSR1)

    def _on_connect(self, client, _, flags, rc):
        self._client.subscribe(f"{MQTT_TOPIC_ROOT}/#", qos=MQTT_QOS)

    def _on_disconnect(self, _1, _2, rc):
        print("disconnected!")
        if rc != 0: print("Network error")
