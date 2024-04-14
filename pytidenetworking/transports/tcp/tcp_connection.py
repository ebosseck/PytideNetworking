# Updated to 2.1.0

from typing import Tuple, List, Union
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from pytidenetworking.connection import Connection
from pytidenetworking.peer import DisconnectReason
from pytidenetworking.transports.tcp.tcp_peer import TCPPeer

from socket import socket, error

from pytidenetworking.utils.exceptions import ArgumentOutOfRangeException
from pytidenetworking.utils.logengine import getLogger

logger = getLogger("TCPConnection")

BYTE_ORDER_LITTLE: Literal['big', 'little'] = "little"
BYTE_ORDER_BIG: Literal['big', 'little'] = "big"

MESSAGE_LENGTH_BYTES = 4 # int

class TCPConnection(Connection):
    """
    TCP Connection to either a TCP Server or TCP Client
    """
    def __init__(self, socket: socket, remoteEndpoint: Tuple[str, int], peer: TCPPeer):
        """
        Initializes the connection

        :param socket: The socket to use for sending / receiving
        :param remoteEndpoint: the remote address
        :param peer: the local peer associated with this connection
        """
        super().__init__()
        self.socket = socket
        self.remoteEndpoint = remoteEndpoint

        self._didReceiveConnect = False

        self.byte_order = BYTE_ORDER_LITTLE

        self.__tcpPeer = peer

        self.sizeBytes: bytes = bytes()
        self.messageBytes: bytes = bytes()
        self.nextMessageSize = 0

    def __hash__(self):
        return self.remoteEndpoint.__hash__()

    def __str__(self):
        return "{}:{}".format(*self.remoteEndpoint)

    def __eq__(self, other):
        if not isinstance(other, TCPConnection):
            return False
        if self is None:
            if other is None:
                return True
            return False
        if other is None:
            return False
        return self.remoteEndpoint == other.remoteEndpoint

    def __ne__(self, other):
        return not self.__eq__(other)

    def send(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int):
        """
        Sends data

        :param dataBuffer: data to send
        :param amount: number of bytes to send
        """
        #TODO: clip dataBuffer to amount ?
        if len(dataBuffer) <= 0:
            raise ArgumentOutOfRangeException()

        realAmount = min(len(dataBuffer), amount)

        try:
            self.__tcpPeer.sendBuffer = bytearray(realAmount.to_bytes(length=MESSAGE_LENGTH_BYTES, byteorder=self.byte_order, signed=True))
            #todo: double check: why signed ?
            self.__tcpPeer.sendBuffer.extend(dataBuffer[:realAmount+1])
            self.socket.sendall(self.__tcpPeer.sendBuffer)
        except error as ex:
            logger.debug(ex)

    def receive(self):
        """Polls the socket and checks if any data was received."""
        tryReceiveMore = True

        while(tryReceiveMore):
            byteCount = 0
            try:
                if self.nextMessageSize > 0:
                    tryReceiveMore, byteCount = self.tryReceiveMessage()
                else:
                    while len(self.sizeBytes) < MESSAGE_LENGTH_BYTES:
                        receivedBytes = self.socket.recv(MESSAGE_LENGTH_BYTES - len(self.sizeBytes))
                        self.sizeBytes += receivedBytes
                        if len(receivedBytes) == 0:
                            tryReceiveMore = False
                            break # No new bytes received

                    self.nextMessageSize = int.from_bytes(self.sizeBytes, self.byte_order, signed=True)
                    if self.nextMessageSize > 0:
                        tryReceiveMore, byteCount = self.tryReceiveMessage()

            except BlockingIOError:
                tryReceiveMore = False # No more data available
            except TimeoutError:
                tryReceiveMore = False
                self.__tcpPeer.onDisconnected(self, DisconnectReason.TimedOut)
            except ConnectionResetError:
                tryReceiveMore = False
                self.__tcpPeer.onDisconnected(self, DisconnectReason.Disconected)
            except InterruptedError or ConnectionAbortedError:
                tryReceiveMore = False
                self.__tcpPeer.onDisconnected(self, DisconnectReason.TransportError)
            except OSError as ex:
                if ex.errno == 10038:
                    tryReceiveMore = False
                    self.__tcpPeer.onDisconnected(self, DisconnectReason.TransportError)
                else:
                    tryReceiveMore = False
                    self.__tcpPeer.onDisconnected(self, DisconnectReason.TransportError)
                    logger.error("Unhandled OS ERROR '{}' : {}".format(ex.errno, ex))
            except Exception as ex:
                tryReceiveMore = False
                self.__tcpPeer.onDisconnected(self, DisconnectReason.TransportError)
                logger.error("Unhandled TCP Exception: {}".format(ex))

            if byteCount > 0:
                self.__tcpPeer.receiveBuffer = self.messageBytes
                self.__tcpPeer.onDataReceived(byteCount, self)
                self.messageBytes = bytes()

    def tryReceiveMessage(self) -> Tuple[bool, int]:
        """
        Attempts to receive a message, returns True and the length of the message, if full message was received, false otherwise
        :return: True and the length of the message, if a full message was received, false otherwise
        """
        try:
            while len(self.messageBytes) < self.nextMessageSize:
                recievedBytes = self.socket.recv(self.nextMessageSize - len(self.messageBytes))
                self.messageBytes += recievedBytes
                if len(recievedBytes) == 0:
                    return False, 0  # No new bytes received
            self.sizeBytes = bytes()
            self.nextMessageSize = 0
            return True, len(self.messageBytes)
        except BlockingIOError:
            return False, 0

    def close(self):
        """
        Closes the connection
        """
        logger.debug("Close Socket")
        self.socket.close()
