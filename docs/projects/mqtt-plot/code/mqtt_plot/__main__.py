from . config import *
from . bk_app import BkApp
from . mqtt_listener import MqttListener
from bokeh.server.server import Server
import os



app = BkApp()
mqtt = MqttListener(app)

# start bokeh server
try:
    url = f"{os.getenv('DNS_NAME', 'iot49.local')}.local:{SERVER_PORT}"
    print(f"starting bokeh server at http://{url}")
    server = Server({'/': app.app}, 
                    num_procs=1, port=SERVER_PORT, 
                    allow_websocket_origin = [ url ])
    server.start()
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
except KeyboardInterrupt:
    print("so long")
