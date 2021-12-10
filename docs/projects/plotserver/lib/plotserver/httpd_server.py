from http.server import HTTPServer, BaseHTTPRequestHandler
from functools import partial

PORT = 8080

css = """\
* {
    font-family: Arial, Helvetica, sans-serif;
}

table {
    font-size: 20px;
    table-layout: fixed;
}

td {
    text-align: left;
    padding: 10px;
}

h1 {
    color: green;
}
"""

class Redirect(BaseHTTPRequestHandler):
    
    def __init__(self, app_dict, *args, **kwargs):
        self._app_dict = app_dict
        super().__init__(*args, **kwargs)
        
    @property
    def app_dict(self):
        return self._app_dict
    
    @property
    def scheme(self):
        # TODO: determine from request
        return "https"
    
    @property
    def host(self):
        return self.headers.get("Host", "localhost")
    
    def app_url(self, app):
        return f"{self.scheme}://{self.host}/plot_{app.port}/{app.app_name}"
    
    def w(self, m):
        if isinstance(m, str):
            m = m.encode()
        self.wfile.write(m)    
    
    def html(self, indent, tag, content):
        return f"{' '*2*indent}<{tag}>{str(content)}</{tag}>\n"
    
    def a(self, url, text):
        return f'<a href="{url}">{text}</a>'
    
    def send_app_list(self):
        with self.app_dict as apps:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.w("<html>\n")
            self.w("  <head>\n")
            self.w("    <style>\n")
            self.w(css)
            self.w("    </style>\n")
            self.w(self.html(2, "title", "PlotServer: Active Applications"))      
            self.w("  </head>\n")
            self.w("  <body>\n")
            if apps.len():
                self.w(self.html(2, "h1", "Active Plot Applications"))
                self.w("    <table>\n")
                for k,v in apps._apps.items():
                    self.w("      <tr>\n")
                    self.w(self.html(4, "td", self.a(self.app_url(v), k)))
                    # self.w(self.html(4, "td", v.port, True))
                    # self.w(self.html(4, "td", v.path, True))
                    url = f"{self.scheme}://{self.host}/plotserver/{k}/shutdown"
                    self.w(self.html(4, "td", self.a(url, "shutdown")))
                    self.w("      </tr>\n")
                self.w("    </table>\n")
            else:
                self.w(self.html(2, "h1", "No Active Plot Applications"))
            self.w("  </body>\n")
            self.w("</html>\n")
        
    def send_app_redirect(self, app_name):
        with self.app_dict as apps:
            app = apps.get(app_name)
            if not app:
                self.send_error(404, f"no such app, '{app_name}'")
                return
            self.send_response(302)
            target = self.app_url(app)
            print(f"redirect {self.path} to {target}")
            self.send_header('Location', target)
            self.end_headers()    
            
    def shutdown_app(self, app_name):
        with self.app_dict as apps:
            apps.remove(app_name)
            self.send_response(302)
            self.send_header('Location', f"{self.scheme}://{self.host}/plotserver")
            self.end_headers()              
        
    def do_GET(self):
        path = self.path[1:]
        if path == '':
            self.send_app_list()
        elif '/' in path:
            app_name, shutdown = path.split('/', 1)
            if shutdown == "shutdown":
                self.shutdown_app(app_name)
        else:
            self.send_app_redirect(path)

            
class HttpdServer(HTTPServer):
    
    def __init__(self, app_dict):
        super().__init__(('', PORT), partial(Redirect, app_dict))
