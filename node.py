from .constants import Roles

class Node:
    """Docstring
    """

    role = Roles.FOLLOWER
    peers, data, clock = [], [], []
    leader_strategies, follower_strategies, candidate_strategies = None, None, None

    @classmethod
    def from_node(cls, data):
        return cls(data)

    def __init__(self, 
                 network, 
                 leader_strategies, 
                 follower_strategies, 
                 candidate_strategies,
                 remote
                ):
        self.network = network
        self.leader_strategies = leader_strategies
        self.follower_strategies = follower_strategies
        self.candidate_strategies = candidate_strategies
        self.remote = remote

    def run(self):
        """Docstring
        """

        # TODO: Execute both functions on different threads.
        # 1. Start a server and listen to request.
        # 2. When there are messages process them. A queue maybe?
        self.init_network()

        # Depends on the {role} varialbe.
        self.perform_role()
    
    def init_network(self):
        """Docstring
        """

        attempt_after = 1
        packet = {
            'data': 'Hello, world',
            'ip': '172.23.54.52',
            'port': '80'
        }

        while True:
            # wait(attemptAfter)
            connected = self.network.attempt_connection(packet)

            if connected:
                return # end thread
            else:
                attempt_after = attempt_after * 2

    
    def perform_role(self):
        """Docstring
        """

        while True:
            self.state.push(self.dataSource.fetch())

            if self.role == Roles.FOLLOWER:
                has_failed = self.follower_strategies.exchange_state()
                if has_failed: self.role = Roles.CANDIDATE

            elif self.role == Roles.CANDIDATE:
                is_elected = self.candidate_strategies.attempt_election()
                if is_elected: self.role = Roles.LEADER
                else: self.role = Roles.FOLLOWER
            
            elif self.role == Roles.LEADER:
                self.leader_strategies.remote_sync()
                self.leader_strategies.update_network()

            else:
                raise Exception(f"Unknown role {self.role}")
