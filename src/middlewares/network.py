from threading import Thread
from collections import defaultdict, deque
import socket
import socketserver
from ..constants import PORT, Headers
import json


class Request:
    def __init__(self, message, address):
        message = json.loads(message)
        
        self.clock = message['clock']
        self.header = message['header']
        self.data = message['data']
        
        self.client_address = address

    def __repr__(self):
        return f'(clock: {self.clock}, header: {self.header}, data: {self.data}'

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
    last_seq = defaultdict(lambda: 0)
    is_connected = False
    clock = 0

    def __init__(self, address=(socket.gethostbyname(socket.gethostname()), PORT)):
        self.address = address
        print(f'Assigned address {address[0]}:{address[1]}!')
        self._establish_connection()
        self._start_servers()
        self.host = self.address[0]
        self.uid = self.get_uid(self.host)

    def unicast(self, msg):

        print(msg.address, self.address[0])
        if msg.address == self.address[0]:
            return

        self.clock += 1
        self.rebuild_message(msg)
        # try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((msg.address, PORT))
            sock.sendall(bytes(msg.get_message(), 'utf-8'))
        # except Exception as ex:
            # print(ex)
            
    def multicast(self, msg):
        self.clock += 1
        self.rebuild_message(msg)
        # TODO: What the heck is this? you're supposed to do leader unicast.
        self.ip_multicast(msg.get_message(), (msg.address, PORT))

    def ip_multicast(self, msg):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(bytes(msg.get_message(), 'utf-8'), (msg.address, PORT))

    def broadcast(self, msg):
        self.clock += 1
        msg = self.rebuild_message(msg)

        broken_ip = self.address[0].split('.')
        address = f'{broken_ip[0]}.{broken_ip[1]}.255.255'

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(bytes(msg.get_message(), 'utf-8'), (address, PORT))

    def rebuild_message(self, msg):
        msg.clock = self.clock
        return msg

    def _establish_connection(self):
        self.is_connected = True

    def _start_servers(self):
        if not self.is_connected:
            raise Exception('Unexpected network behaviour.')

        def compare_and_push(request):
            if request.clock == self.last_seq[request.client_address] + 1:
                self.request_queue.append(request)
                self.last_seq[request.client_address] += 1

                req_list = sorted(self.hold_back_queue[request.client_address], key=lambda x: x.clock)
                self.hold_back_queue[request.client_address].clear()

                for req in req_list:
                    if req.clock == self.last_seq[request.client_address] + 1:
                        self.request_queue.append(req)
                        self.last_seq[request.client_address] += 1
                    else:
                        self.hold_back_queue[request.client_address].append(req)
            else:
                self.hold_back_queue[request.client_address].append(request)
                negative_ack = Message(Headers.MSG_MISSING, self.last_seq[request.client_address] + 1, request.client_address)
                self.unicast(negative_ack)

        def udp_server():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', PORT))

            while True:
                request, address = sock.recvfrom(8192)
                request = Request(request, address[0])

                self.peers.append(self.get_uid(request.client_address))
                self.peers = list(set(self.peers))

                compare_and_push(request)

        class RequestHandler(socketserver.BaseRequestHandler):
            def handle(this):
                self.peers.append(self.get_uid(this.client_address[0]))
                self.peers = list(set(self.peers))

                request = Request(this.request.recv(8192), this.client_address[0])
                compare_and_push(request)

        self.tcp_server = socketserver.ThreadingTCPServer(self.address, RequestHandler)
        
        Thread(target=udp_server).start()
        Thread(target=self.tcp_server.serve_forever).start()

        print('Servers up and running...')

    def get_request(self):
        if self.request_queue:
            self.clock += 1
            return self.request_queue.popleft()
        else:
            return None

    def get_neighbor(self):
        ring = sorted(self.peers + [self.uid])
        return ring[ring.index(self.uid) - 1]

    def get_peers(self):
        return self.peers

    def get_uid(self, address):
        return int(''.join(address.split('.')))
        
    def disconnect(self):
        self.tcp_server.shutdown()
        