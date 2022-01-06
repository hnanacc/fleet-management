from .node import Node
from .middlewares.network import Network
from .middlewares.logger import Logger
from .strategies.follower import FollowerStrategies
from .strategies.leader import LeaderStrategies
from .strategies.candidate import CandidateStrategies
from .remote_node import Remote

def main():
    node = Node(
        Network(),
        FollowerStrategies(),
        LeaderStrategies(),
        CandidateStrategies(),
        Remote()
    )

    try:
        node.run()
    except Exception:
        Logger.log("Something happened!")

if __name__ == '__main__':
    main()