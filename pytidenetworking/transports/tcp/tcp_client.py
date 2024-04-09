# Updated to 2.1.0

from pytidenetworking.connection import Connection
from pytidenetworking.transports.iclient import IClient
from pytidenetworking.transports.tcp.tcp_connection import TCPConnection
from pytidenetworking.transports.tcp.tcp_peer import TCPPeer, DEFAULT_SOCKET_BUFFER_SIZE
from pytidenetworking.utils.eventhandler import EventHandler

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_SNDBUF, SO_RCVBUF, IPPROTO_TCP, TCP_NODELAY

class TCPClient(TCPPeer, IClient):
    """
    A client which can connect to a TcpServer
    """
    def __init__(self, socketBufferSize: int = DEFAULT_SOCKET_BUFFER_SIZE):
        """
        A client which can connect to a TcpServer

        :param socketBufferSize: Buffer size for the underlying socket
        """
        super(TCPClient, self).__init__(socketBufferSize=socketBufferSize)

        self.Connected: EventHandler = EventHandler()
        self.ConnectionFailed: EventHandler = EventHandler()

        self.tcpConnection = None

    def connect(self, host: str, port: int) -> [bool, Connection, str]:
        """
        Connect this client to a remote host

        :param host: host address to connect to
        :param port: host port to connect to
        :return: True if the connection was successfully created, the connection created and an error string if the
        connection attempt failed
        """
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(
            SOL_SOCKET,
            SO_SNDBUF,
            self.socketBufferSize)
        self.socket.setsockopt(
            SOL_SOCKET,
            SO_RCVBUF,
            self.socketBufferSize)
        self.socket.setsockopt(
            IPPROTO_TCP,
            TCP_NODELAY,
            1
        )

        self.socket.connect((host, port))
        self.socket.setblocking(False)

        self.tcpConnection = TCPConnection(self.socket, (host, port), self)
        self.onConnected()

        return True, self.tcpConnection, ""

    def poll(self):
        """
        Polls the Client's connection for newly arrived bytes
        :return:
        """
        if self.tcpConnection is not None:
            self.tcpConnection.receive()

    def disconnect(self):
        """
        Disconnects this client and closes the connection
        :return:
        """
        self.socket.close()
        self.tcpConnection = None

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

    def onDataReceived(self, amount: int, fromConnection: TCPConnection):
        """
        Invokes the data received event

        :param amount: length of data received
        :param fromConnection: Connection the date is received from
        """
        self.DataReceived(self.receiveBuffer, amount, fromConnection)