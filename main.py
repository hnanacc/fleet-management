from src.node import Node
from src.middlewares.network import Network
from src.middlewares.logger import Logger
from src.strategies.fault import FaultStrategies
from src.strategies.leader import LeaderStrategies
from src.middlewares.remote import Remote
from src.middlewares.data_source import DataSource

def main():
    # host, port = input('Enter the (host:port): ').strip().split(':')
    
    node = Node(
        Network(),
        LeaderStrategies(),
        FaultStrategies(),
        Remote(),
        DataSource()
    )

    node.run()

    # try:
    #     node.run()
    # except Exception:
    #     Logger.log("Something happened!")

if __name__ == '__main__':
    main()