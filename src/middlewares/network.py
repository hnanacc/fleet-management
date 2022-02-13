from threading import Thread
from collections import defaultdict, deque
import socket
import socketserver
from ..constants import PORT, Headers
import json


class Request:
    def __init__(self, message, address):
        message = json.loads(message)
        
        self.header = message['header']
        self.data = message['data']
        
        self.client_address = address

    def __repr__(self):
        return f'(addr: {self.client_address}, header: {self.header}, data: {self.data})'

class Message:
    def __init__(self, header, data, address):
        self.header = header
        self.data = data
        self.address = address
    
    def get_message(self):
        return json.dumps({
            'header': self.header,
            'data': self.data,
        })

class Network:

    """Docstring
    """

    peers = []
    request_queue = deque()
    hold_back_queue = defaultdict(list)
    last_seq = defaultdict(lambda: 0)
    group_clock = 0
    is_connected = False

    def __init__(self, address=(socket.gethostbyname(socket.gethostname()), PORT)):
        self.address = address
        print(f'Assigned address {address[0]}:{address[1]}!')
        self._establish_connection()
        self._start_servers()
        self.host = self.address[0]
        self.uid = self.get_uid(self.host)

    def unicast(self, msg):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((msg.address, PORT))
                sock.sendall(bytes(msg.get_message(), 'utf-8'))
        except Exception as ex:
            print(ex)
            
    def multicast(self, msg):
        self.group_clock += 1
        msg.data['group_clock'] = self.group_clock

        broken_ip = self.address[0].split('.')
        address = f'{broken_ip[0]}.{broken_ip[1]}.255.255'

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(bytes(msg.get_message(), 'utf-8'), (address, PORT))

    def broadcast(self, msg):
        broken_ip = self.address[0].split('.')
        address = f'{broken_ip[0]}.{broken_ip[1]}.255.255'

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(bytes(msg.get_message(), 'utf-8'), (address, PORT))

    def _establish_connection(self):
        self.is_connected = True

    def _start_servers(self):
        if not self.is_connected:
            raise Exception('Unexpected network behaviour.')

        def compare_and_push(request):
            # there is only one group.
            if request.header == Headers.GROUP_UPDATE:
                if self.last_seq[request.client_address] + 1 == request.data['group_clock']:
                    self.request_queue.append(request)
                    self.last_seq[request.client_address] += 1

                    # Clear the hold back queue here.
                    held_out = sorted(self.hold_back_queue[request.client_address], key=lambda x: x.data['group_clock'])
                    self.hold_back_queue[request.client_address].clear()

                    for req in held_out:
                        if self.last_seq[request.client_address] + 1 == req.data['group_clock']:
                            self.request_queue.append(req)
                            self.last_seq[request.client_address] += 1
                        else:
                            self.hold_back_queue.append(req)
                            neg_ack = Message(Headers.MSG_MISSING, { 'missed': self.last_seq[request.client_address] + 1 }, request.client_address)
                            self.unicast(neg_ack)
                elif self.last_seq[request.client_address] < request.data['group_clock']:
                    self.hold_back_queue[request.client_address].append(request)
                    neg_ack = Message(Headers.MSG_MISSING, { 'missed': self.last_seq[request.client_address] + 1 }, request.client_address)
                    self.unicast(neg_ack)
                else:
                    pass
            else: 
                self.request_queue.append(request)


        def udp_server():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', PORT))

            while True:
                request, address = sock.recvfrom(8192)
                request = Request(request, address[0])

                self.peers.append(request.client_address)
                self.peers = list(set(self.peers))

                print('About to invoke')

                compare_and_push(request)

        class RequestHandler(socketserver.BaseRequestHandler):
            def handle(this):
                self.peers.append(this.client_address[0])
                self.peers = list(set(self.peers))

                request = Request(this.request.recv(8192), this.client_address[0])
                self.request_queue.append(request)

        self.tcp_server = socketserver.ThreadingTCPServer(self.address, RequestHandler)
        
        Thread(target=udp_server).start()
        Thread(target=self.tcp_server.serve_forever).start()

        print('Servers up and running...')

    def get_request(self):
        if self.request_queue:
            return self.request_queue.popleft()
        else:
            return None

    def get_neighbor(self):
        print(self.peers)
        ring = sorted(self.peers, key=lambda x: self.get_uid(x))
        return ring[ring.index(self.address[0]) - 1]

    def get_peers(self):
        return self.peers

    def get_uid(self, address):
        return int(''.join(address.split('.')))
        
    def disconnect(self):
        self.tcp_server.shutdown()
        