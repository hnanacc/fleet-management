from enum import Enum

class Roles(str, Enum):
    FOLLOWER = 'follower'
    LEADER = 'leader'


class Headers(str, Enum):
    PRESENCE_ACK = 'PRESENCE_ACK'               # Response after presence broadcast.
    LEADER_ELECTION = 'LEADER_ELECTION'         # For everything related to election.
    DATA_EXCHANGE = 'DATA_EXCHANGE'             # For sharing state with leader.
    
    GROUP_UPDATE = 'GROUP_UPDATE'               # Multicast messages sent by leader.
    MSG_MISSING = 'MSG_MISSING'                 # Negative ack when message missing.

    PRESENCE_BROADCAST = 'PRESENCE_BROADCAST'   # Initial broadcast to show presence.


PORT = 4334
