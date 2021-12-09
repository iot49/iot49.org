from threading import Lock
import os, subprocess


class App:
    
    def __init__(self, app_name, path, port):
        self._app_name = app_name
        self._path = path
        self._port = port
        self._proc = None
    
    def start(self):
        if self._port:
            self.shutdown()
            self._proc = subprocess.Popen(["bokeh", "serve", "--port", str(self.port), self.path])
            print(f"bokeh serve --port {self._port} {self._path}")
        else:
            print(f"{self.app_name}.start() failed: port = {self.port}")
    
    def shutdown(self):
        if self._proc:
            print("kill", self._proc)
            self._proc.kill()
        self._proc = None
        
    @property
    def app_name(self):
        return self._app_name
    
    @property
    def port(self):
        return self._port
    
    @property
    def path(self):
        return self._path

    @property
    def is_running(self):
        return self._proc != None
    
    
class AppDict:
    
    def __init__(self, port_range: set):
        """port_range: set of available ports"""
        self._port_range = port_range
        self._apps = {}
        self._lock = Lock()
        
    def __enter__(self):
        self._lock.acquire()
        return self
    
    def __exit__(self, *args):
        self._lock.release()
        
    def add(self, app_name, path):
        app = self._apps.get(app_name)
        if app:
            # app already defined
            return app
        ports_in_use = { a.port for a in self._apps.values() }
        available_ports = self._port_range - ports_in_use
        if len(available_ports) == 0:
            raise ValueError(f"Cannot create '{app_name}' - no free ports")
        # add new app
        app = self._apps[app.app_name] = App(app_name, path, list(available_ports)[0])
        return app
        
    def remove(self, app_name):
        app = self._apps.get(app_name)
        if app:
            app.shutdown()
            try:
                os.remove(app.path)
            except:
                pass
            del self._apps[app_name]
        
    def has(self, app_name):
        return app_name in self._apps
        
    def get(self, app_name):
        return self._apps.get(app_name)
    
    def len(self):
        return len(self._apps)