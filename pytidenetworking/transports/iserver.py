# Updated to 2.1.0

from pytidenetworking.transports.ipeer import IPeer, EventHandler


class IServer(IPeer):
    """
    Defines methods, properties, and events which every transport's server must implement
    """
    def __init__(self):
        """
        Initializes the server
        """
        super(IServer, self).__init__()
        self.Connected: EventHandler = EventHandler()
        """
        Invoked when a connection is established at the transport level
        """
        self._port: int = -1

    @property
    def port(self) -> int:
        return self._port

    def start(self, port: int):
        """
        Starts the transport and begins listening for connections

        :param port: Port to listen on
        :return:
        """
        pass

    def close(self, connection):
        """
        Closes an active connection

        :param connection: the connection to close
        :return:
        """
        pass

    def shutdown(self):
        """
        Stop Listening and close all existing connections
        :return:
        """
        pass