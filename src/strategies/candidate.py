class CandidateStrategies:

    election_initiated = False

    def init_election(self, network):
        port = 4444 if network.address[1] == 4443 else 4443
        network.broadcast(f'LEADER_ELECT:{port}', ('0.0.0.0', port))
        self.election_initiated = True

    def process_request(self, request, network):
        if request is None:
            return

        if request.header == 'LEADER_ELECT':
            network.unicast("I don't want to be.", request.client_address)
