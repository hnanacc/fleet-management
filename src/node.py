import time
import random
from .constants import Roles, Headers
from middlewares.network import Message

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

    leader_strategies, follower_strategies = None, None

    def __init__(self,
                 network,
                 follower_strategies, 
                 leader_strategies, 
                 fault_strategies,
                 remote,
                 data_source
                ):
        self.network = network
        self.leader_strategies = leader_strategies
        self.follower_strategies = follower_strategies
        self.fault_strategies = fault_strategies
        self.remote = remote
        self.data_source = data_source
        self.uid = int(self.network.host.split('.').join())

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
        message = Message({
            'header': Headers.PRESENCE_BROADCAST,
            'data': ''
        })
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

            self._process_request(request) # generic.

            if self.role == Roles.FOLLOWER:
                self.follower_strategies.process_request(request, self.network)

            
            elif self.role == Roles.LEADER:
                self.leader_strategies.process_request(request, self.network)

                self.leader_strategies.remote_sync()
                self.leader_strategies.update_network()

            else:
                raise Exception(f"Unknown role {self.role}")

    def update_state(self, key, new_state):
        print(f'Got a new state {new_state} at {key}')
        pass

    def _process_request(self, request):
        # 1. Request types - LEADER_ELECT, DATA_EX, ..., EX_CLOCK
        # self.network.host - Gives the host address of the node.
        # We can use ip-address to generate IDs for each node.
        # Sum is not a good heuristic, 1.1.1.1 and 2.2.0.0 has sum 4.
        # One option is to remove the dots, 1.1.1.1 = 1111. Unique.
        if request is None:
            return
        
        if request.header == Headers.LEADER_ELECTION:
            self.ring=self.network.get_ring()
            neighbor = self.get_neighbor(self.ring, self.my_uid, 'left')
            self.leader_election(self,request,neighbor)

        elif request.header == Headers.DATA_EXCHANGE:
            # some code.

        elif request.header == Headers.GROUP_UPDATE:
            pass

        elif request.header == Headers.MULTICAST_ONBEHALF:
            pass

        elif request.header == Headers.PRESENCE_ACK:
            pass

        elif request.header == Headers.PRESENCE_BROADCAST:
            pass

        else:
            print(f'Request with invalid header: {request.header} received!')

    def initiate_election(self):
        self.network.broadcast('election')

    def resolve_election(self, election_message):  
        neighbor = self.network.get_neighbor()

        if self.role == Roles.LEADER:
            pass
        else:
            election_message = Message()

            if mid < uid:
                election_message.uid = self.uid 
                self.unicast(election_message,neighbor)
            if(mid>uid):
                election_message
            pass

        if election_message['isLeader']:
            self.leader_uid = election_message['uid']
            self.participant = False
            self.network.unicast(election_message, neighbor)

        elif election_message['uid'] < self.uid and not self.participant:
            new_message = Message({
                'isLeader': False
            })
            new_election_message = { 
            'mid':self.uid, 
            'isLeader': False }
            self.participant = True
            self.network.unicast(new_election_message,neighbor)

        elif election_message['mid'] > self.uid:
            self.participant =True
            #ring_socket.sendto(json.dumps(election_message),neighbor)
            self.network.unicast(election_message,neighbor)
        elif election_message['mid'] == self.uid:
            self.leader_uid =self.uid
            new_election_message = {
                'mid':self.uid,
                'isLeader': True
            }
            self.participant = False
            self.role = Roles.LEADER
            #ring_socket.sendto(json.dumps(new_election_message),neighbor)
            self.network.unicast(new_election_message,neighbor)
        pass

    def initiate_election(self, neighbor):
        self.participant = True

        election_message = {
            'mid':self.uid,
            'isLeader': False
        }

        self.network.unicast(election_message, neighbor)

    def _attempt_fault_with_probability(self, prob):
        if random.random() < prob:
            self.fault_strategies.execute_random_fault()
