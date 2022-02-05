from ..constants import Headers

class FollowerStrategies:
    def exchange_state(self):
        pass

    def process_request(self, request, network):
        if request.headers == Headers.LEADER_ELECTION:
            # check uid is none.
            # leader function.
            # uid is not none and leader not crashed.
            # send leader uid.
            