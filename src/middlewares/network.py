from threading import Thread
from collections import defaultdict, deque
import socket
import socketserver
from ..constants import PORT, Headers, Roles
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

    leader_uid = None
    leader_address = None
    role = Roles.FOLLOWER
    participant = False

    def __init__(self, address=(socket.gethostbyname(socket.gethostname()), PORT)):
        self.address = address
        print(f'Assigned address {address[0]}:{address[1]}!')
        self._establish_connection()
        self._start_servers()
        self.host = self.address[0]
        self.uid = self.get_uid(self.host)
        self.peers.append(self.host)

    def initiate_election(self):
        neighbor = self.get_neighbor()
        message = Message(Headers.LEADER_ELECTION, {}, neighbor)
        message.data['uid'] = self.uid
        message.data['leader_address'] = self.host
        message.data['isLeader'] = (self.uid == self.leader_uid)
        self.unicast(message)
        print('Election Initiated...')

    def resolve_election(self, request):
        neighbor = self.get_neighbor()
        new_message = Message(Headers.LEADER_ELECTION, {}, neighbor)
        pb_uid = int(request.data['uid'])

        if request.data['isLeader']:
            new_message.data['uid'] = request.data['uid']
            new_message.data['isLeader'] = request.data['isLeader']
            new_message.data['leader_address'] = request.data['leader_address']

            self.leader_uid = pb_uid
            self.leader_address = request.data['leader_address']
            self.participant = False
            self.unicast(new_message)
    
        elif pb_uid < self.uid and not self.participant:
            new_message.data['uid'] = self.uid
            new_message.data['isLeader'] = False
            new_message.data['leader_address'] = request.data['leader_address']

            self.participant = True
            self.unicast(new_message)

        elif pb_uid > self.uid:
            new_message.data['uid'] = request.data['uid']
            new_message.data['isLeader'] = request.data['isLeader']
            new_message.data['leader_address'] = request.data['leader_address']

            self.participant = True
            self.unicast(new_message)
    
        elif pb_uid == self.uid:
            new_message.data['uid'] = self.uid
            new_message.data['isLeader'] = True
            new_message.data['leader_address'] = self.host

            self.leader_uid = self.uid
            self.leader_address = self.host
            self.role = Roles.LEADER
            self.participant = False

            self.unicast(new_message)

    def unicast(self, msg):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                sock.connect((msg.address, PORT))
                sock.sendall(bytes(msg.get_message(), 'utf-8'))
        except socket.error as ex:
            if msg.address in self.peers and msg.address != self.host:
                    self.peers.remove(msg.address)
            
            if self.get_uid(msg.address) == self.leader_uid and not self.participant:
                self.leader_uid = None
                self.leader_address = None
                self.initiate_election()
                
    def multicast(self, msg):
        if msg.data.get('group_clock') is None:
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
                            self.hold_back_queue[request.client_address].append(req)
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
        ring = sorted(self.peers, key=lambda x: self.get_uid(x))
        return ring[ring.index(self.address[0]) - 1]

    def get_peers(self):
        return self.peers

    def get_uid(self, address):
        return int(''.join(address.split('.')))

    def get_leader_uid(self):
        return self.leader_uid
    
    def set_leader_uid(self, uid):
        self.leader_uid = uid

    def get_leader_address(self):
        return self.leader_address

    def set_leader_address(self, leader_address):
        self.leader_address = leader_address

    def get_role(self):
        return self.role
        
    def disconnect(self):
        self.tcp_server.shutdown()
        