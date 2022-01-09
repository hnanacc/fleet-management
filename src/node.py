import time
import random
from .constants import Roles

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
        pass

    def _attempt_fault_with_probability(self, prob):
        if random.random() < prob:
            self.fault_strategies.execute_random_fault()
