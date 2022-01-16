from . layouts import line_plot
from . config import *
from bokeh.models import ColumnDataSource
from bokeh.layouts import column
import queue, importlib, time


class BkApp:
    
    def __init__(self):
        self._queue = queue.Queue()
        # create default appearance
        self._layout = None
        self.update_appearance()
        # flag _update that ploat has changed
        self._plot_changed = False
        
    @property
    def column_names(self):
        # column names of current plot
        return self._column_names
    
    def add_data(self, data_frame):
        # add row of data to current plot
        self._queue.put_nowait(data_frame)
        
    def update_appearance(self, 
               spec = "line_plot", 
               column_names = [ "x", "data" ], 
               args = { "title": "MQTT Plot" }, 
               rollover = 200):
        self._spec = spec
        self._column_names = column_names
        self._args = args
        self._rollover = rollover
        # drain data queue
        with self._queue.mutex:
            self._queue.queue.clear()
        # flag _update that plot has changed
        self._plot_changed = True
    
    def app(self, doc):
        self._plot_changed = False
        # create new app, silently abandon old one (no more updates)
        self._layout = column(self._appearance())      
        doc.add_root(self._layout)
        # kludge to call update only on most recent instance of app
        self._version = version = time.monotonic()
        def _updater():
            if self._version == version:
                self._update()
        doc.add_periodic_callback(_updater, SERVER_UPDATE_PLOT_MS)
        
    def _update(self):
        # call this regularly to move data from receive queue to column_data_source
        if self._plot_changed:
            self._layout.children[0] = self._appearance()
            self._plot_changed = False
        try:
            while not self._queue.empty():
                df = self._queue.get()
                self._data_source.stream(df, rollover=self._rollover)
        except Exception as e:
            print(f"*** Plot.update: {e}")
            
    def _appearance(self):
        template = importlib.import_module(f'{line_plot.__package__}.{self._spec}')
        self._data_source = ColumnDataSource(data={ t: [] for t in self._column_names })  
        return template.layout(self._data_source, self._args)
         
