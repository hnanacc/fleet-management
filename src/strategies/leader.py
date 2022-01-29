class LeaderStrategies:
    global_seq = 0
    def remote_sync(self):
        pass

    def update_network(self):
        pass

    def process_request(self, request, network):
        if request.header == 'MULTICAST_REQ':
            # format the message here.
            message, group_address = request.content, request.group_address
            network.ip_multicast(message, group_address)