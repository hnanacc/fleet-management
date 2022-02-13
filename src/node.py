import time
import random
from .constants import Roles, Headers
from .middlewares.network import Message

class Node:
    """Docstring
    """

    role = Roles.FOLLOWER
    state = {
        'data': [],
    }
    participant = False
    leader_uid = None
    uid = None
    group_events = dict()

    leader_strategies = None

    def __init__(self,
                 network,
                 leader_strategies, 
                 fault_strategies,
                 remote,
                 data_source
                ):
        self.network = network
        self.leader_strategies = leader_strategies
        self.fault_strategies = fault_strategies
        self.remote = remote
        self.data_source = data_source
        self.uid = int(''.join(self.network.host.split('.')))

    def run(self):
        """Docstring
        """

        # Announce presence.
        self.announce_presence()

        # Start election.
        if self.leader_uid is None:
            self.initiate_election()

        # Depends on the {role} varialbe.
        self.perform_role()

    def announce_presence(self):
        message = Message(Headers.PRESENCE_BROADCAST, {}, '')
        self.network.broadcast(message)
    
    def perform_role(self):
        """Docstring
        """

        while True:

            # self._attempt_fault_with_probability(0.5)
            # self.update_state('data', self.data_source.fetch_data())

            # print('Peers list:', self.network.get_peers())
            time.sleep(1)

            request = self.network.get_request()
            
            if request is not None:
                print('From node:', request)

            self.process_request(request) # generic.

            if self.role == Roles.LEADER:
                self.leader_strategies.remote_sync()


    def update_state(self, key, new_state):
        print(f'Got a new state {new_state} at {key}')
        pass

    def process_request(self, request):
        
        if request is None:
            return
        
        if request.header == Headers.LEADER_ELECTION:
            print(f'[Leader Election] {request}')
            self.resolve_election(request)
            print(f'[Elected] {self.leader_uid}!!')

        elif request.header == Headers.DATA_EXCHANGE:
            if self.role != Roles.LEADER:
                return
            
            print(request)

        elif request.header == Headers.GROUP_UPDATE:
            print(f'[Multicast Event] {request}')

        elif request.header == Headers.PRESENCE_ACK:
            self.leader_uid = request.data['leader_uid']

        elif request.header == Headers.PRESENCE_BROADCAST:
            self.network.unicast(Message(Headers.PRESENCE_ACK, { 'leader_uid': self.leader_uid }, request.client_address))

        elif request.header == Headers.MSG_MISSING:
            # self.network.unicast(Message(Headers.DATA_EXCHANGE, {}, request.client_address))
            pass

        else:
            print(f'Request with invalid header: {request.header} received!')

    def initiate_election(self):
        print('Initiate election')
        neighbor = self.network.get_neighbor()
        message = Message(Headers.LEADER_ELECTION, {}, neighbor)
        message.data['uid'] = self.uid
        message.data['isLeader'] = (self.uid == self.leader_uid)
        self.network.unicast(message)

    def resolve_election(self, request):
        print('Came into resolve election.............................................')
        neighbor = self.network.get_neighbor()
        new_message = Message(Headers.LEADER_ELECTION, {}, neighbor)
        pb_uid = int(request.data['uid'])

        # isLeader: true

        if request.data['isLeader']:
            new_message.data['uid'] = request.data['uid']
            new_message.data['isLeader'] = request.data['isLeader']

            self.leader_uid = pb_uid 
            self.participant = False
            self.network.unicast(new_message)

        if pb_uid < self.uid and not self.participant:
            new_message.data['uid'] = self.uid
            new_message.data['isLeader'] = False

            self.participant = True
            self.network.unicast(new_message)

        elif pb_uid > self.uid:
            new_message.data['uid'] = request.data['uid']
            new_message.data['isLeader'] = request.data['isLeader']

            self.participant = True
            self.network.unicast(new_message)
        
        elif pb_uid == self.uid:
            new_message.data['uid'] = self.uid
            new_message.data['isLeader'] = True

            self.leader_uid = self.uid
            self.role = Roles.LEADER
            self.participant = False

            self.network.unicast(new_message)

    def _attempt_fault_with_probability(self, prob):
        if random.random() < prob:
            self.fault_strategies.execute_random_fault()
