import time
import random
from .constants import Roles
import socket
import json
from middlewares.network import Network

class Node:
    """Docstring
    """

    role = Roles.CANDIDATE
    state = {
        'data': [],
    }

    leader_strategies, follower_strategies, candidate_strategies = None, None, None

    def __init__(self,
                 network,
                 follower_strategies, 
                 leader_strategies, 
                 candidate_strategies,
                 fault_strategies,
                 remote,
                 data_source
                ):
        self.network = network
        self.leader_strategies = leader_strategies
        self.follower_strategies = follower_strategies
        self.candidate_strategies = candidate_strategies
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

            elif self.role == Roles.CANDIDATE:
                self.candidate_strategies.process_request(request, self.network)

                if not self.candidate_strategies.election_initiated:
                    self.candidate_strategies.init_election(self.network)
            
            elif self.role == Roles.LEADER:
                self.leader_strategies.process_request(request, self.network)

                self.leader_strategies.remote_sync()
                self.leader_strategies.update_network()

            else:
                raise Exception(f"Unknown role {self.role}")

    def update_state(self, key, new_state):
        # print(f'Got a new state {new_state} at {key}')
        pass

    def _process_request(self, request):
        # 1. Request types - LEADER_ELECT, DATA_EX, ..., EX_CLOCK
        # self.network.host - Gives the host address of the node.
        # We can use ip-address to generate IDs for each node.
        # Sum is not a good heuristic, 1.1.1.1 and 2.2.0.0 has sum 4.
        # One option is to remove the dots, 1.1.1.1 = 1111. Unique.
        
        if request.header == 'LEADER_ELECT':
            # leader election.
            ip=self.network.host
            self.leader_election(self)
            pass
        elif request.header == 'DATA_EX':
            pass

        # server - 8080 udp, tcp
        # client - client - random port
        pass

    def leader_election(self):
        my_uid = self.network.host  #discard all dot between ip 
        #ring_port =4040
        leader_uid=''
        participant = False
        members=self.network.get_peers()  #get a list of peers ( Harshal check this var)
        
        ring = self.form_ring(members)
        neighbor = self.get_neighbor(ring, my_uid, 'left')
        
        #ring_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #ring_socket.bind((self.network.host,ring_port)) #use original ip for connection
        print(f'Node is running at{my_uid}:{ring_port}')

        print ('\n Waiting to receive election message... \n')
        data,address = ring_socket.recv(4096)
        election_message = json.loads(data.decode())

        if election_message['isLeader']:
            leader_uid = election_message['mid']
            participant = False
            #ring_socket.sendto(json.dumps(election_message),neighbor)
            Network.unicast(json.dumps(election_message),neighbor)

        if election_message['mid']< my_uid and not participant:
            new_election_message = { 
            'mid':my_uid, 
            'isLeader': False }
            participant = True
            #ring_socket.sendto(json.dumps(new_election_message),neighbor)
            Network.unicast(json.dumps(new_election_message),neighbor)
        elif election_message['mid'] > my_uid:
            participant =True
            #ring_socket.sendto(json.dumps(election_message),neighbor)
            Network.unicast(json.dumps(election_message),neighbor)
        elif election_message['mid'] == my_uid:
            leader_uid =my_uid
            new_election_message = {
                'mid':my_uid,
                'isLeader': True
            }
            participant = False
            #ring_socket.sendto(json.dumps(new_election_message),neighbor)
            Network.unicast(json.dumps(new_election_message),neighbor)
        pass

    def form_ring(members):
        sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
        sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
        return sorted_ip_ring

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
