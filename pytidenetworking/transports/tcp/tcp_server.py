from typing import List, Tuple, Dict

from pytidenetworking.connection import Connection
from pytidenetworking.message_base import MessageHeader, HEADER_BITMASK
from pytidenetworking.transports.iserver import IServer
from pytidenetworking.transports.tcp.tcp_connection import TCPConnection
from pytidenetworking.transports.tcp.tcp_peer import TCPPeer, DEFAULT_SOCKET_BUFFER_SIZE

from socket import socket, SOL_SOCKET, SO_REUSEADDR, AF_INET, SOCK_STREAM, NI_NUMERICHOST, NI_NUMERICSERV,\
    SO_SNDBUF, SO_RCVBUF, getnameinfo, IPPROTO_TCP, TCP_NODELAY

from pytidenetworking.utils.logengine import getLogger

logger = getLogger()

class TCPServer(TCPPeer, IServer):
    """
    A server which can accept connections from TCP Clients
    """
    def __init__(self, socketBufferSize: int = DEFAULT_SOCKET_BUFFER_SIZE, listenAddress = ""):
        """
        Initializes the TCP Server

        :param socketBufferSize: Buffer size for the underlying socket
        :param listenAddress: The listen address of the server, defaults to any
        """
        super(TCPServer, self).__init__(socketBufferSize=socketBufferSize)

        self.__isRunning = False
        self.listenAddress = listenAddress

        self.flags = NI_NUMERICHOST | NI_NUMERICSERV

        self.connections: Dict[Tuple[str, int], Connection] = {}
        self.closedConnections: List[Tuple[str, int]] = []

    @property
    def maxPendingConnections(self):
        """
        :return: the maximum number of pending connections
        """
        return 5

    def start(self, port: int):
        """
        Starts the transport and begins listening for connections

        :param port: Port to listen on
        :return:
        """
        if self.__isRunning:
            self.stopListening()

        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

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
        self.socket.setblocking(False)

        self._port = port

        self.socket.bind((self.listenAddress, self.port))
        self.socket.listen(self.maxPendingConnections)

        self.__isRunning = True

    def poll(self):
        """
        Initiates handling of messages received & connection attempts
        :return:
        """
        if not self.__isRunning:
            return

        for endPoint in self.closedConnections:
            try:
                logger.debug("Deleting Connection {}".format(endPoint))
                del self.connections[endPoint]
            except KeyError:
                logger.debug("Deleting Connection {} failed with Key Error".format(endPoint))
                #TODO: Handle & Debug why it is happening
                pass

        self.closedConnections.clear()

        self.__accept()

        for connection in self.connections.values():
            connection.receive()

        for endPoint in self.closedConnections:
            try:
                logger.debug("Deleting Connection {}".format(endPoint))
                del self.connections[endPoint]
            except KeyError:
                logger.debug("Deleting Connection {} failed with Key Error".format(endPoint))
                #TODO: Handle & Debug why it is happening
                pass

        self.closedConnections.clear()

    def __accept(self):
        """
        Accepts any pending connections
        :return:
        """
        try:
            connectionSocket, connectionAddress = self.socket.accept()
            host, port = getnameinfo(connectionAddress, self.flags)
            connectionSocket.setblocking(False)
            endpoint = (host, int(port))
            if endpoint not in self.connections:
                connection = TCPConnection(connectionSocket, endpoint, self)
                self.connections[connection.remoteEndpoint] = connection
                self.onConnected(connection=connection)
            else:
                connectionSocket.close()
        except BlockingIOError:
            pass

    def stopListening(self):
        """
        Stop listening for connections

        :return:
        """
        if not self.__isRunning:
            return
        self.__isRunning = False
        self.socket.close()

    def close(self, connection):
        """
        Closes an active connection

        :param connection: the connection to close
        :return:
        """
        if isinstance(connection, TCPConnection):
            if connection.remoteEndpoint in self.connections.keys():
                self.closedConnections.append(connection.remoteEndpoint)
                connection.close()
                logger.debug("Connection Closed")

    def shutdown(self):
        """
        Stop Listening and close all existing connections
        :return:
        """
        self.stopListening()
        self.connections.clear()

    def onConnected(self, connection):
        """
        Invokes the connected event
        :param connection: the successfully established connection
        :return:
        """
        self.Connected(connection)

    def onDataReceived(self, amount: int, fromConnection: TCPConnection):
        """
        Invokes the data received events
        :param amount: number of bytes received
        :param fromConnection: connection which received the data
        :return:
        """
        if self.receiveBuffer[0] & HEADER_BITMASK == MessageHeader.Connect:
            if fromConnection._didReceiveConnect:
                return
            fromConnection._didReceiveConnect = True

        self.DataReceived(self.receiveBuffer, amount, fromConnection)
