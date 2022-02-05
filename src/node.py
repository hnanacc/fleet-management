import time
import random
from .constants import Roles, Headers

class Node:
    """Docstring
    """

    role = Roles.FOLLOWER
    state = {
        'data': [],
    }
    participant = False
    leader_uid=''
    my_uid=None
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

    def run(self):
        """Docstring
        """

        # Depends on the {role} varialbe.
        self.perform_role()
    
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

            self._process_request(request)

            if self.role == Roles.FOLLOWER:
                self.follower_strategies.process_request(request, self.network)

                has_failed = self.follower_strategies.exchange_state()
                if has_failed: self.role = Roles.CANDIDATE

            #elif self.role == Roles.CANDIDATE:
            #    self.candidate_strategies.process_request(request, self.network)

            #    if not self.candidate_strategies.election_initiated:
            #        self.candidate_strategies.init_election(self.network)
            
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
            self.my_uid = self.network.host  
            self.ring=self.network.get_ring()
            neighbor = self.get_neighbor(self.ring, self.my_uid, 'left')
            self.leader_election(self,request,neighbor)

        elif request.header == Headers.DATA_EXCHANGE:
            pass

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


    def leader_election(self,data,neighbor):  
        
        #ring = self.form_ring(members)
        
        print(f'Node is running at{self.my_uid}:{self.network.port}')

        print ('\n Waiting to receive election message... \n')
        #data,address = ring_socket.recv(4096)
        election_message = self.network.get_request(data.content)

        if election_message['isLeader']:
            self.leader_uid = election_message['mid']
            self.participant = False
            #ring_socket.sendto(json.dumps(election_message),neighbor)
            self.network.unicast(election_message,neighbor)
        elif election_message['mid']< self.my_uid and not self.participant:
            new_election_message = { 
            'mid':self.my_uid, 
            'isLeader': False }
            self.participant = True
            #ring_socket.sendto(json.dumps(new_election_message),neighbor)
            self.network.unicast(new_election_message,neighbor)
        elif election_message['mid'] > self.my_uid:
            self.participant =True
            #ring_socket.sendto(json.dumps(election_message),neighbor)
            self.network.unicast(election_message,neighbor)
        elif election_message['mid'] == self.my_uid:
            self.leader_uid =self.my_uid
            new_election_message = {
                'mid':self.my_uid,
                'isLeader': True
            }
            self.participant = False
            self.role = Roles.LEADER
            #ring_socket.sendto(json.dumps(new_election_message),neighbor)
            self.network.unicast(new_election_message,neighbor)
        pass

    def initiate_election(self,neighbor):
        self.participant=True
        election_message = {
            'mid':self.my_uid,
            'isLeader': False
        }
        self.network.unicast(election_message,neighbor)

    #def form_ring(members):
    #    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    #    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    #    return sorted_ip_ring

    def get_neighbor(ring,current_node_ip,direction):
        current_node_index = ring.index(current_node_ip) if current_node_ip in ring else -1
        if current_node_index != -1:
            if direction == 'left':
                if current_node_index + 1 == len(ring):
                    return ring[0]
                else:
                    return ring[current_node_index +1]
            else:
                if current_node_index == 0:
                    return ring[len(ring)-1]
                else:
                    return ring[current_node_index -1]
        else:
            return None

    def _attempt_fault_with_probability(self, prob):
        if random.random() < prob:
            self.fault_strategies.execute_random_fault()
