from enum import Enum

class Roles(Enum):
    FOLLOWER = 'follower'
    LEADER = 'leader'
    CANDIDATE = 'candidate'
