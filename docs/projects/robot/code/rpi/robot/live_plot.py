from bokeh.models import ColumnDataSource, Toggle, Column
from bokeh.plotting import figure
from bokeh.palettes import Category10_10 as palette
from bokeh.io import show
# import asyncio
import itertools, os


class LivePlot:
    
    def __init__(self, x_name, y_names, rollover=None, update_interval_ms=10, **figure_args):
        self._rollover = rollover
        self._update_interval_ms = update_interval_ms
        
        # trace names        
        self._trace_names = [ y_names ] if isinstance(y_names, str) else y_names.copy()
        self._trace_names.append(x_name)
        
        # data source
        df = { trace: [] for trace in self._trace_names }
        self._data_source = data = ColumnDataSource(data=df)
        
        # plot figure
        figure_defaults = {
            'x_axis_label': x_name,
            'plot_width': 800,
            'plot_height': 500, 
        }
        self._plot_figure = figure(**{**figure_defaults, **figure_args})
        colors = itertools.cycle(palette)  
        for y_name, color in zip(y_names, colors):
            self._plot_figure.line(x_name, y_name, source=data, legend_label=y_name, color=color)
            
        self._plot_figure.legend.location = "top_left"
        self._plot_figure.legend.click_policy="hide"

        
    def app(self, doc):
        self._pause_button = Toggle(label = "Pause", button_type = "success")
        doc.add_root(Column(self._plot_figure, self._pause_button))
        doc.add_periodic_callback(self._update, self._update_interval_ms)        
        
    def show(self, data_source):
        # hack to get notebook_url
        self._data_queue = data_source
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        port = os.getenv('JUPYTER_PORT', 8888)
        show(self.app, notebook_url=f"http://{ip}:{port}")
        return 
        
    def _update(self):
        if self._pause_button.active:
            return
        while not self._data_queue.empty():
            new_data = self._data_queue.get()
            df = { t: [new_data.get(t)] for t in self._trace_names }
            self._data_source.stream(df, rollover=self._rollover)
            