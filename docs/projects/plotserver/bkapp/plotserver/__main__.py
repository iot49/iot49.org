from .bkapp import bkapp
from bokeh.server.server import Server

server = Server({'/': bkapp}, num_procs=1)
server.start()

server.io_loop.add_callback(server.show, "/")
server.io_loop.start()


print("DONE")