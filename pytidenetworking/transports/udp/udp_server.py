# Updated to 2.1.0

from typing import Dict, Tuple, Union, List

from pytidenetworking.connection import Connection
from pytidenetworking.message_base import MessageHeader, HEADER_BITMASK
from pytidenetworking.transports.iserver import IServer
from pytidenetworking.transports.udp.udp_connection import UDPConnection
from pytidenetworking.transports.udp.udp_peer import UDPPeer, SocketMode, _DEFAULT_SOCKET_BUFFER_SIZE


class UDPServer(UDPPeer, IServer):
    """
    A server which can accept connections from UdpClients

    :param mode: Whether to create an IPv4 only, IPv6 only, or dual-mode socket
    :param socketBufferSize: How big the socket's send and receive buffers should be
    :param listenAddress: Address to listen on, empty string means any
    """
    def __init__(self, mode: SocketMode = SocketMode.Both, socketBufferSize: int = _DEFAULT_SOCKET_BUFFER_SIZE, listenAddress: str = ''):
        super(UDPServer, self).__init__(mode, socketBufferSize, listenAddress)

        self._port: int = -1
        self.connections: Dict[Tuple[str, int], Connection] = {}

    @property
    def port(self) -> int:
        """
        Port this server is active on
        """
        return self._port

    def start(self, port: int):
        self._port = port
        self.connections.clear()
        self.openSocket(port=port)

    def handleConnectionAttempt(self, fromEndpoint: Tuple[str, int]) -> bool:
        """
        Decides what to do with a connection attempt.

        :param connection: The connection to accept or reject.
        :returns: Whether or not the connection attempt was a new connection.
        """
        if fromEndpoint in self.connections:
            return False
        connection = UDPConnection(fromEndpoint, self)
        self.connections[fromEndpoint] = connection
        self.onConnected(connection)
        return True

    def close(self, connection: Connection):
        if isinstance(connection, UDPConnection):
            if connection.remoteEndpoint in self.connections.keys():
                del self.connections[connection.remoteEndpoint]

    def shutdown(self):
        self.closeSocket()
        self.connections.clear()

    def onConnected(self, connection: Connection):
        """
        Invokes the Connected event
        :param connection: The successfully established connection
        """
        self.Connected(connection)

    def onDataReceived(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int, fromEndPoint: Tuple[str, int]):
        """
        Handles received data

        :param dataBuffer: A byte array containing the received data
        :param amount: the number of bytes received
        :param fromEndpoint: the endpoint the bytes were received from
        :return:
        """
        if (dataBuffer[0] & HEADER_BITMASK) == MessageHeader.Connect and not self.handleConnectionAttempt(fromEndPoint):
            return

        if fromEndPoint in self.connections.keys():
            c = self.connections[fromEndPoint]
            if not c.isNotConnected:
                self.DataReceived(dataBuffer, amount, c)