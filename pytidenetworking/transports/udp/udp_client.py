# Updated to 2.1.0

from typing import Union, List, Tuple

from pytidenetworking.connection import Connection
from pytidenetworking.transports.iclient import IClient
from pytidenetworking.transports.udp.udp_connection import UDPConnection
from pytidenetworking.transports.udp.udp_peer import UDPPeer, SocketMode, _DEFAULT_SOCKET_BUFFER_SIZE


class UDPClient(UDPPeer, IClient):
    
    def __init__(self, mode: SocketMode = SocketMode.Both, socketBufferSize: int = _DEFAULT_SOCKET_BUFFER_SIZE, listenAddress: str = ''):
        super(UDPClient, self).__init__(mode, socketBufferSize, listenAddress)
        self.udpConnection: UDPConnection = None


    def connect(self, hostAddress: str, port: int) -> [bool, Connection, str]:
        """
        Connect this client to a remote host

        :param host: host address to connect to
        :param port: host port to connect to
        :return: True if the connection was successfully created, the connection created and an error string if the
        connection attempt failed
        """

        #TODO error checks ?
        self.openSocket()
        self.udpConnection = UDPConnection((hostAddress, port), self)
        self.onConnected()
        return True, self.udpConnection, ""

    def disconnect(self):
        """
        Disconnects this client and closes the connection
        :return:
        """
        self.closeSocket()

    def onConnected(self):
        """
        Invokes the connected event
        """
        self.Connected()

    def onConnectionFailed(self):
        """
        Invokes the connection failed event
        """
        self.ConnectionFailed()

    def onDataReceived(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int,
                       fromEndPoint: Tuple[str, int]):
        """
        Invokes the data received event

        :param amount: length of data received
        :param fromConnection: Connection the date is received from
        """
        if self.udpConnection.remoteEndpoint == fromEndPoint and not self.udpConnection.isNotConnected:
            self.DataReceived(dataBuffer, amount, self.udpConnection)