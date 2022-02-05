from enum import Enum

class Roles(Enum):
    FOLLOWER = 'follower'
    LEADER = 'leader'


class Headers(Enum):
    PRESENCE_ACK = 'PRESENCE_ACK'               # Response after presence broadcast.
    LEADER_ELECTION = 'LEADER_ELECTION'         # For everything related to election.
    DATA_EXCHANGE = 'DATA_EXCHANGE'             # For sharing state with leader.
    
    GROUP_UPDATE = 'GROUP_UPDATE'               # Multicast messages sent by leader.
    MULTICAST_ONBEHALF = 'MULTICAST_ONBEHALF'   # Multicast request to leader.

    PRESENCE_BROADCAST = 'PRESENCE_BROADCAST'   # Initial broadcast to show presence.


PORT = 4334
