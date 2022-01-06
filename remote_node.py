from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

PORT = 8080

class Handler(BaseHTTPRequestHandler):
    def _send_data(self, data, status, headers):
        if isinstance(data, str):
            data = bytes(data, 'utf-8')
        
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)

        self.send_header('Content-Length', str(len(data)))
        self.end_headers()

        self.wfile.write(data)
        self.wfile.flush()
    
    def do_GET(self):
        self._send_data(
            f'Got GET request at {self.path}',
            200,
            { 'Content-Type': 'text/plain'}
        )
    
    def do_POST(self):
        print(self.rfile.readlines())
        self._send_data(
            f'Got POST request at {self.path}',
            200,
            { 'Content-Type': 'text/plain'}
        )

with ThreadingHTTPServer(('', PORT), Handler) as server:
    print(f'Server listening at port {PORT}')
    server.serve_forever()
