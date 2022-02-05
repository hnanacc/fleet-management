from ..constants import Headers

class LeaderStrategies:
    global_seq = 0
    def remote_sync(self):
        pass

    def update_network(self):
        pass

    def process_request(self, request, network):
        if request.header == Headers.DATA_EXCHANGE:
            pass