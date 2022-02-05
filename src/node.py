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
    ring = None

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
        self.leader_election()

        # Depends on the {role} varialbe.
        self.perform_role()

    def announce_presence(self):
        message = Message(Headers.PRESENCE_ACK, '', '')
        self.network.broadcast(message)
    
    def perform_role(self):
        """Docstring
        """

        while True:

            self._attempt_fault_with_probability(0.5)
            self.update_state('data', self.data_source.fetch_data())

            time.sleep(1)

            request = self.network.get_request()
            
            if request is not None:
                print(request.raw, request.client_address)

            self.process_request(request) # generic.

            if self.role == Roles.LEADER:
                self.leader_strategies.remote_sync()

            else:
                raise Exception(f"Unknown role {self.role}")

    def update_state(self, key, new_state):
        print(f'Got a new state {new_state} at {key}')
        pass

    def process_request(self, request):
        
        if request is None:
            return
        
        if request.header == Headers.LEADER_ELECTION:
            self.resolve_election(self, request)

        elif request.header == Headers.DATA_EXCHANGE:
            if self.role != Roles.LEADER:
                return
            
            self.update_state(request.data)

        elif request.header == Headers.MULTICAST_ONBEHALF:
            request.data.global_id = self.global_counter
            new_message = Message(Headers.GROUP_UPDATE, request.data, request.mc_address)
            self.network.multicast(new_message)
            self.global_counter += 1 # total order

        elif request.header == Headers.GROUP_UPDATE:
            # TODO: What is the update_state function.
            self.update_state(request.data)

        elif request.header == Headers.PRESENCE_ACK:
            pass

        elif request.header == Headers.PRESENCE_BROADCAST:
            self.unicast(Message(Headers.PRESENCE_ACK, '', request.client_address))

        else:
            print(f'Request with invalid header: {request.header} received!')

    def initiate_election(self):
        neighbor = self.network.get_neighbor()
        message = Message(Headers.LEADER_ELECTION, self.uid, neighbor)
        self.network.unicast(message)

    def resolve_election(self, request):  
        neighbor = self.network.get_neighbor()
        new_message = Message(Headers.LEADER_ELECTION, '', neighbor)
        pb_uid = int(request.data)

        if request.isLeader:
            self.leader_uid = pb_uid 
            self.participant = False
            self.network.unicast(new_message)

        if pb_uid < self.uid and not self.participant:
            new_message.data = self.uid
            new_message.isLeader = False
            self.participant = True

            self.network.unicast(new_message)

        elif pb_uid > self.uid:
            self.participant = True
            self.network.unicast(new_message)
        
        elif pb_uid == self.uid:
            self.leader_uid = self.uid
            self.role = Roles.LEADER
            
            new_message.data = self.uid
            new_message.isLeader = True
            self.participant = False

            self.network.unicast(new_message)

    def initiate_election(self, neighbor):
        self.participant = True

        msg = Message(
            Headers.LEADER_ELECTION,
            self.uid,
            neighbor
        )

        msg.isLeader = False
        self.network.unicast(msg)

    def _attempt_fault_with_probability(self, prob):
        if random.random() < prob:
            self.fault_strategies.execute_random_fault()
