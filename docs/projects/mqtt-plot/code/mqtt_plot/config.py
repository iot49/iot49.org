# config.py

import os

# mqtt

MQTT_BROKER = os.getenv('HOST_IP')
MQTT_PORT = 1883
MQTT_QOS = 0
# all topics related to mqtt_plot start with this prefix
MQTT_TOPIC_ROOT = "public/vis"

# bokeh server

SERVER_PORT = 5006
# document updated ever PLOT_MS milliseconds
SERVER_UPDATE_PLOT_MS = 50
