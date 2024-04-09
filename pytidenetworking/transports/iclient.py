# Updated to 2.1.0

from pytidenetworking.connection import Connection
from pytidenetworking.transports.ipeer import IPeer, EventHandler


class IClient(IPeer):
    """
    Defines methods, properties, and events which every transport's client must implement.
    """
    def __init__(self):
        super(IClient, self).__init__()
        self.Connected: EventHandler = EventHandler()
        """
        Invoked when a connection is established at the transport level.
        """
        self.ConnectionFailed: EventHandler = EventHandler()
        """
        Invoked when a connection attempt fails at the transport level.
        """

    def connect(self, hostAddress: str, port: int) -> [bool, Connection, str]:
        """
        Starts the transport and attempts to connect to the given host address.
        :param hostAddress: The host address to connect to.
        :return: True, if no issue occured, the pending connection, and an error message if any issue occured
        """
        return False

    def disconnect(self):
        """
        Closes the connection to the server
        """
        pass
