import time
import random
from .constants import Roles, Headers
from .middlewares.network import Message
from collections import defaultdict

class Node:
    """Docstring
    """

    state = {
        'data': [],
        'group_events': []
    }
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
        """Performs the functions based on the current role.
        """

        while True:

            self.update_state('data', self.data_source.fetch_data())

            time.sleep(1)

            request = self.network.get_request()

            if self.network.get_leader_uid() and self.network.get_leader_uid() != self.network.uid:
                self.network.unicast(Message(Headers.DATA_EXCHANGE, self.state['data'][-1], self.network.get_leader_address()))

            # Send random multicast messages.
            if random.random() > 0.95:
                self.network.multicast(Message(Headers.GROUP_UPDATE, { 'random': 'event' }, ''))

            # Create the multicast sequence.
            mc_seq = defaultdict(list)
            for ev in self.state['group_events']:
                mc_seq[ev.client_address].append(str(ev.data['group_clock']))

            mc_list = []
            for client in mc_seq:
                mc_list.append(f'{client}:({", ".join(mc_seq[client])})')

            # Print the status.
            print('\n---\n')
            print(f'[ IP Address      ]: {self.network.host}')
            print(f'[ Peers List      ]: {self.network.get_peers()}')
            print(f'[ Current Leader  ]: {self.network.get_leader_address()}')
            print(f'[ Current Request ]: {request}')
            print(f'[ Multicast Seq   ]: {" ".join(mc_list)}')
            
            self.process_request(request)

            if self.network.get_role() == Roles.LEADER:
                self.leader_strategies.remote_sync()


    def update_state(self, key, new_state):
        self.state[key].append(new_state)

    def process_request(self, request):
        if request is None:
            return
        
        if request.header == Headers.LEADER_ELECTION:
            if self.network.get_leader_uid() is None:
                self.network.resolve_election(request)

        elif request.header == Headers.DATA_EXCHANGE:
            if self.network.get_role() != Roles.LEADER:
                return
            
        elif request.header == Headers.GROUP_UPDATE:
            self.update_state('group_events', request)

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
            for msg in self.state['group_events']:
                if msg.client_address == self.network.host and msg.data['group_clock'] == request.data['missed']:
                    new_message = Message(Headers.GROUP_UPDATE, msg.data, '')
                    self.network.multicast(new_message)

        else:
            print(f'Request with invalid header: {request.header} received!')

    def _attempt_fault_with_probability(self, prob):
        if random.random() < prob:
            self.fault_strategies.execute_random_fault()
