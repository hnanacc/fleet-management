import time
import random
from .constants import Roles, Headers
from .middlewares.network import Message

class Node:
    """Docstring
    """

    state = {
        'data': [],
    }
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
        if self.network.get_leader_uid() is None:
            self.network.initiate_election()

        # Depends on the {role} varialbe.
        self.perform_role()

    def announce_presence(self):
        message = Message(Headers.PRESENCE_BROADCAST, {}, '')
        self.network.broadcast(message)
    
    def perform_role(self):
        """Docstring
        """

        while True:

            self._attempt_fault_with_probability(0.5)
            # self.update_state('data', self.data_source.fetch_data())

            print(f'[Current Leader] {self.network.get_leader_uid()}')

            time.sleep(1)

            request = self.network.get_request()

            # if self.network.get_leader_uid() is None:
                # self.network.initiate_election()

            if self.network.get_leader_uid() and self.network.get_leader_uid() != self.network.uid:
                self.network.unicast(Message(Headers.DATA_EXCHANGE, { 'ui': 'ui' }, self.network.get_leader_address()))
            
            if request is not None:
                print('From node:', request)

            self.process_request(request) # generic.

            if self.network.get_role() == Roles.LEADER:
                self.leader_strategies.remote_sync()


    def update_state(self, key, new_state):
        print(f'Got a new state {new_state} at {key}')

    def process_request(self, request):
        if request is None:
            return
        
        if request.header == Headers.LEADER_ELECTION:
            print(f'[Leader Election] {request}')
            if self.network.get_leader_uid() is None:
                self.network.resolve_election(request)
                print(f'[Elected] {self.network.get_leader_uid()}!!')

        elif request.header == Headers.DATA_EXCHANGE:
            if self.network.get_role() != Roles.LEADER:
                return
            
            print(request)

        elif request.header == Headers.GROUP_UPDATE:
            print(f'[Multicast Event] {request}')

        elif request.header == Headers.PRESENCE_ACK:
            if request.data['leader_uid'] is not None:
                self.network.set_leader_uid(request.data['leader_uid'])
                self.network.set_leader_address(request.data['leader_address'])

        elif request.header == Headers.PRESENCE_BROADCAST:
            self.network.unicast(Message(Headers.PRESENCE_ACK, { 
                'leader_uid': self.network.get_leader_uid(), 
                'leader_address': self.network.get_leader_address() 
            }, request.client_address))

        elif request.header == Headers.MSG_MISSING:
            # self.network.unicast(Message(Headers.DATA_EXCHANGE, {}, request.client_address))
            pass

        else:
            print(f'Request with invalid header: {request.header} received!')

    def _attempt_fault_with_probability(self, prob):
        if random.random() < prob:
            self.fault_strategies.execute_random_fault()
