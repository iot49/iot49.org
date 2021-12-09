import paho.mqtt.client as mqtt
import json, urllib.request
import os, sys

sys.path.append(os.path.expandvars('$IOT_PROJECTS/plotserver/lib'))

from plot_proxy import PlotProxy
from config import *

class LinePlotProxy(PlotProxy):
    
    def __init__(self, app_name, column_names, *, rollover=None, update_interval=0.1, **figure_args):
        super().__init__(app_name, 
            "line_plot", "LinePlot", 
            column_names, rollover, update_interval, **figure_args)
        
    def add_row(self, row):
        topic = f"{TOPIC_ROOT}/call/{self._app_name}"
        payload = ("add_row", [row], {})
        self._mqttc.publish(topic, json.dumps(payload))
