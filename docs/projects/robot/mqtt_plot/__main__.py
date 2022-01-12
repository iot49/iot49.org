from . config import *
from . mqtt_listener import MqttListener
from . layouts import line_plot
from bokeh.server.server import Server
from time import sleep
import os, importlib, sys


# bokeh app
def bkapp(doc):
    global mqtt
    layout = importlib.import_module(f'{line_plot.__package__}.{mqtt.layout}')
    doc.add_root(layout.layout(mqtt.column_data_source, mqtt.args))
    doc.add_periodic_callback(mqtt.update, SERVER_UPDATE_PLOT_MS)

# listen for data
mqtt = MqttListener()

# wait for mqtt data  
print("MQTT Plot: waiting for mqtt data")
sys.stdout.flush()
while not mqtt.column_data_source:
    sleep(1)
    
# start bokeh server

url = f"{os.getenv('DNS_NAME', 'iot49.local')}.local:{SERVER_PORT}"

print(f"starting bokeh server at http://{url}")

try:
    server = Server({'/': bkapp}, 
                    num_procs=1, port=SERVER_PORT, 
                    allow_websocket_origin = [ url ])
    server.start()
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
except KeyboardInterrupt:
    print("so long")
except Exception as e:
    print("exit", e)