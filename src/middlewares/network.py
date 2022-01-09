from threading import Thread
from collections import deque
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from socketserver import ThreadingUDPServer, ThreadingTCPServer, BaseRequestHandler

class Request:
    def __init__(self, data, client_address):
        self.raw = data
        self.client_address = client_address
        self.header = str(data[:32], 'utf-8')
        self.message = str(data[32:], 'utf-8')

class Network:

    """Docstring
    """

    peers = []
    msg_queue = deque()
    is_connected = False

    def __init__(self, address):
        self.address = address
        self._establish_connection()
        self._start_servers()

    def unicast(self, msg, address):
        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.connect(address)
            sock.sendall(bytes(msg, 'utf-8'))
            
    def multicast(self, msg, addresses):
        for address in addresses:
            self.unicast(msg, address)

    def broadcast(self, msg, address):
        with socket(AF_INET, SOCK_DGRAM) as sock:
            sock.sendto(bytes(msg, 'utf-8'), address)

    def _establish_connection(self):
        self.is_connected = True

    def _start_servers(self):
        if not self.is_connected:
            raise Exception('Unexpected network behaviour.')

        class RequestHandler(BaseRequestHandler):
            def handle(this):
                message = None
                if this.server.socket_type is SOCK_DGRAM:
                    message = this.request[0].strip()
                else:
                    message = this.request.recv(4096)
                
                self.msg_queue.append(Request(message, this.client_address))

        self.tcp_server = ThreadingTCPServer(self.address, RequestHandler)
        self.udp_server = ThreadingUDPServer(self.address, RequestHandler)

        Thread(target=self.tcp_server.serve_forever, daemon=True).start()
        Thread(target=self.udp_server.serve_forever, daemon=True).start()

        print(f'TCP server running at {self.tcp_server.socket}')
        print(f'UDP server running at {str(self.udp_server.socket)}')

    def get_request(self):
        if self.msg_queue:
            return self.msg_queue.popleft()
        else:
            return None
        
    def disconnect(self):
        self.tcp_server.shutdown()
        self.udp_server.shutdown()
        