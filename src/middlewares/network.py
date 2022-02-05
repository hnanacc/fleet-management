from threading import Thread
from collections import defaultdict, deque
from socket import socket, gethostbyname, gethostname, AF_INET, SOCK_STREAM, SOCK_DGRAM
from socketserver import ThreadingUDPServer, ThreadingTCPServer, BaseRequestHandler
from ..constants import PORT, Headers
import json


class Request:
    def __init__(self, message):
        message = json.loads(message)
        for key in message.keys():
            self[key] = message[key]

class Message:
    def __init__(self, header, data, address):
        self.header = header
        self.data = data
        self.address = address
    
    def get_message(self):
        return json.dumps({
            'header': self.header,
            'data': self.data,
            'clock': self.clock
        })

class Network:

    """Docstring
    """

    peers = []
    request_queue = deque()
    hold_back_queue = defaultdict(list)
    last_seq = dict()
    is_connected = False
    clock = 0

    def __init__(self, address=(gethostbyname(gethostname()), PORT)):
        self.address = address
        print(f'Assigned address {address[0]}:{address[1]}!')
        self._establish_connection()
        self._start_servers()
        self.host = self.address[0]

    def unicast(self, msg):
        self.clock += 1
        self.rebuild_message(msg)

        with socket(AF_INET, SOCK_STREAM) as sock:
            sock.connect(msg.address)
            sock.sendall(bytes(msg.get_message(), 'utf-8'))
            
    def multicast(self, msg):
        # send a request to the leader with MULTICAST header.
        # Looking for total ordering. BC only that makes sense.
        self.clock += 1
        self.rebuild_message(msg)
        self.unicast(msg.get_message(), msg.address)

    def ip_multicast(self, msg, group_address):
        # do some message formatting.
        with socket(AF_INET, SOCK_DGRAM) as sock:
            sock.sendto(bytes(msg.get_message(), 'utf-8'), group_address)
        pass

    def broadcast(self, msg):
        self.clock += 1
        msg = self.rebuild_message(msg)

        broken_ip = self.address[0].split('.')
        address = broken_ip[0] + broken_ip[1] + '.0.0'

        with socket(AF_INET, SOCK_DGRAM) as sock:
            sock.sendto(bytes(msg.get_message(), 'utf-8'), (address, PORT))

    def rebuild_message(self, msg):
        msg.clock = self.clock
        msg.some = ''
        return msg

    def _establish_connection(self):
        self.is_connected = True

    def _start_servers(self):
        if not self.is_connected:
            raise Exception('Unexpected network behaviour.')

        class RequestHandler(BaseRequestHandler):
            def handle(this):
                if this.server.socket_type is SOCK_DGRAM:
                    request = Request(this.request[0].strip(), this.client_address)
                    if request.header.endswith('BROADCAST'):
                        self.request_queue.append(request)
                    else:
                        if request.seq == self.last_seq[this.client_address] + 1:
                            self.request_queue.append(request)
                            self.last_seq[this.client_address] += 1
                            # handle hold back queue.
                            req_list = sorted(self.hold_back_queue[this.client_address],
                                                        key=lambda x: x.seq)
                            self.hold_back_queue[this.client_address].clear()
                            for req in req_list:
                                if req.seq == self.last_seq[this.client_address] + 1:
                                    self.request_queue.append(req)
                                    self.last_seq[this.client_address] += 1
                                else:
                                    self.hold_back_queue[this.client_address].append(req)

                        else:
                            self.hold_back_queue[this.client_address].append(request)
                            negative_ack = 'MULTICAST MISSING' + self.last_seq[this.client_address] + 1
                            self.unicast(negative_ack, this.client_address)
                else:
                    request = Request(this.request.recv(4096), this.client_address)
                    self.request_queue.append(request)

        self.tcp_server = ThreadingTCPServer(self.address, RequestHandler)
        self.udp_server = ThreadingUDPServer(self.address, RequestHandler)

        Thread(target=self.tcp_server.serve_forever, daemon=True).start()
        Thread(target=self.udp_server.serve_forever, daemon=True).start()

        print(f'TCP server running at {self.tcp_server.socket}')
        print(f'UDP server running at {str(self.udp_server.socket)}')

    def get_request(self):
        if self.request_queue:
            self.clock += 1
            return self.request_queue.popleft()
        else:
            return None

    def get_neighbor(self):
        ring = sorted(self.peers, key=lambda x: x.uid)
        return ring[ring.index(self.uid) - 1]
        
        
    def disconnect(self):
        self.tcp_server.shutdown()
        self.udp_server.shutdown()
        