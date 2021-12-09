from plot_app import PlotApp
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, Toggle, Column
from bokeh.palettes import Category10_10 as palette
import itertools, queue


class LinePlot(PlotApp):
    
    def __init__(self, app_name, column_names, rollover=None, update_interval=0.1, **figure_args):
        self.column_names = column_names
        self.rollover = rollover
        self.update_interval = update_interval
        self.figure_args = figure_args
        self.row_queue = queue.Queue()
        super().__init__(app_name)
        
    def do_add_row(self, row):
        if isinstance(row, list):
            row = dict(zip(self.column_names, row))
        self.row_queue.put_nowait(row)
        
    def app(self, doc):
        try:
            column_names = self.column_names

            # data source
            df = { trace: [] for trace in column_names }
            data_source = ColumnDataSource(data=df)     

            # figure
            figure_defaults = {
                'x_axis_label': column_names[0],
                'plot_width': 800,
                'plot_height': 500, 
            }
            fig = figure(**{**figure_defaults, **self.figure_args})
            colors = itertools.cycle(palette)  
            for y_name, color in zip(column_names[1:], colors):
                fig.line(column_names[0], y_name, source=data_source, legend_label=y_name, color=color)
            fig.legend.location = "top_left"
            fig.legend.click_policy = "hide"

            # update
            def update():
                # copy rows from data_queue to data_source
                nonlocal self, data_source
                self.loop()
                try:
                    while not self.row_queue.empty():
                        new_data = self.row_queue.get()
                        df = { c: [new_data.get(c)] for c in self.column_names }
                        data_source.stream(df, rollover=self.rollover)
                except Exception as e:
                    print(f"*** update: {e}")
                    
            # app
            doc.add_root(Column(fig, ))
            doc.add_periodic_callback(update, int(1000*self.update_interval)) 
        except Exception as e:
            print(f"*** app: {e}")
