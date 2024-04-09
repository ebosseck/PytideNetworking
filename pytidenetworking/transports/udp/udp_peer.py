# Updated to 2.1.0

from enum import IntEnum
import socket as so
from socket import socket
from typing import Tuple, List, Union

from pytidenetworking.connection import Connection
from pytidenetworking.peer import DisconnectReason
from pytidenetworking.transports.ipeer import IPeer
from pytidenetworking.utils.exceptions import ArgumentOutOfRangeException
from pytidenetworking.utils.logengine import getLogger

logger = getLogger("UDPConnection")

class SocketMode(IntEnum):
    Both = 0,
    """Dual mode, allows for both IPv4 and IPv6"""
    IPv4Only = 1,
    """IPv4 only"""
    IPv6Only = 2
    """IPv6 only"""

_DEFAULT_SOCKET_BUFFER_SIZE = 1024 * 1024 # 1 MB
_MIN_SOCKET_BUFFER_SIZE = 256 * 1024 # 256 KB
__RECEIVE_POLLING_TIME = 500000 # 0.5 seconds

class UDPPeer(IPeer):

    def __init__(self, mode: SocketMode, socketBufferSize: int, listenAddress: str= ""):
        """
        Initializes the transport

        :param mode: Whether to create an IPv4 only, IPv6 only, or dual-mode socket
        :param socketBufferSize: How big the socket's send and receive buffers should be
        """
        super(UDPPeer, self).__init__()
        if socketBufferSize < _MIN_SOCKET_BUFFER_SIZE:
            raise ArgumentOutOfRangeException()

        self.mode: SocketMode = mode
        self.socketBufferSize: int = socketBufferSize

        self.receivedData = bytearray()
        self.socket: socket = None
        self.__isRunning = False

        self.listen_address = listenAddress

        self.remoteEndpoint: Tuple[str, int] = None

    def poll(self):
        self.receive()

    def openSocket(self, listenAddress=None, port: int = 0):
        if listenAddress is None:
            listenAddress = self.listen_address

        if self.__isRunning:
            self.closeSocket()

        if self.mode == SocketMode.IPv4Only:
            self.socket = socket(so.AF_INET, so.SOCK_DGRAM, so.IPPROTO_UDP)

        elif self.mode == SocketMode.IPv6Only:
            self.socket = socket(so.AF_INET6, so.SOCK_DGRAM, so.IPPROTO_UDP)
        else:
            self.socket = socket(so.AF_INET, so.SOCK_DGRAM)

        self.socket.setsockopt(
            so.SOL_SOCKET,
            so.SO_SNDBUF,
            self.socketBufferSize)
        self.socket.setsockopt(
            so.SOL_SOCKET,
            so.SO_RCVBUF,
            self.socketBufferSize)

        self.socket.setblocking(False)

        self.socket.bind((listenAddress, port))
        self.remoteEndpoint = (self.listen_address, 0)
        self.__isRunning = True

    def closeSocket(self):
        """
        Closes the socket and stops the transport
        """
        if not self.__isRunning:
            return
        self.__isRunning = False
        self.socket.close()

    def receive(self):
        if not self.__isRunning:
            return

        tryReceiveMore: bool = True
        while tryReceiveMore:
            byteCount: int = 0
            try:
                self.receivedData, self.remoteEndpoint = self.socket.recvfrom(self.socketBufferSize)
                byteCount = len(self.receivedData)
            except BlockingIOError:
                tryReceiveMore = False  # No more data available
            except TimeoutError:
                pass
            except ConnectionResetError:
                pass
            except InterruptedError or ConnectionAbortedError:
                tryReceiveMore = False
            except OSError as ex:
                if ex.errno == 10038:
                    tryReceiveMore = False
                if ex.errno == 11: #EAGAIN
                    tryReceiveMore = False
                else:
                    logger.error("Unhandled OS ERROR '{}' : {}".format(ex.errno, ex))
            except Exception as ex:
                logger.error("Unhandled UDP Exception: {}".format(ex))

            if byteCount > 0:
                self.onDataReceived(self.receivedData, byteCount, self.remoteEndpoint)

    def send(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int, toEndPoint: Tuple[str, int]):
        try:
            if self.__isRunning:
                self.socket.sendto(dataBuffer[:amount], toEndPoint)
        except Exception as ex:
            logger.debug("Exception occured while sending UDP packet: {}".format(ex))

    def onDataReceived(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int, fromEndPoint: Tuple[str, int]):
        """
        Handles received data

        :param dataBuffer: A byte array containing the received data
        :param amount: the number of bytes received
        :param fromEndpoint: the endpoint the bytes were received from
        :return:
        """
        # Not implemented here
        pass

    def onDisconnected(self, connection: Connection, reason: Union[DisconnectReason, int]):
        self.Disconnected(connection, reason)
