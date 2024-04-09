# Updated to 2.1.0

from typing import List, Optional, TYPE_CHECKING, Union

from socket import socket

from pytidenetworking.transports.ipeer import IPeer
from pytidenetworking.utils.eventhandler import EventHandler
from pytidenetworking.utils.exceptions import ArgumentOutOfRangeException
from ...connection import Connection
from ...peer import DisconnectReason

if TYPE_CHECKING:
    from .tcp_connection import TCPConnection

DEFAULT_SOCKET_BUFFER_SIZE = 1024**2
MINIMUM_SOCKET_BUFFER_SIZE = 256*1024

class TCPPeer(IPeer):
    """
    Provides common functionality for TCP Client + TCP Server
    """
    def __init__(self, socketBufferSize: int = DEFAULT_SOCKET_BUFFER_SIZE):
        """
        Initializes the transport

        :param socketBufferSize: Buffer size for the underlying socket
        """
        super().__init__()

        if socketBufferSize < MINIMUM_SOCKET_BUFFER_SIZE:
            raise ArgumentOutOfRangeException()

        self.socketBufferSize = socketBufferSize

        self.receiveBuffer: bytearray = bytearray(self.socketBufferSize)
        self.sendBuffer: bytearray = bytearray(self.socketBufferSize + 4)

        self.socket: Optional[socket] = None

    def onDataReceived(self, amount: int, fromConnection: "TCPConnection"):
        """
        Handles received data

        :param amount: the number of bytes received
        :param fromConnection: the connection the bytes were received from
        :return:
        """
        # Not implemented here
        pass

    def onDisconnected(self, connection: Connection, reason: Union[DisconnectReason, int]):
        self.Disconnected(connection, reason)
