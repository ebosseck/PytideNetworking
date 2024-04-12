# Updated to 2.1.0

from enum import IntEnum
from queue import PriorityQueue
from time import time
from typing import List, TYPE_CHECKING, Union

from pytidenetworking.utils.delayed_events import DelayedEvent
from .message import Message, createFromBytes as createRawMessage
from .message_base import MessageHeader, MIN_NOTIFY_BYTES, MIN_RELIABLE_BYTES, HEADER_BITMASK

from .constants import *

if TYPE_CHECKING:

    from pytidenetworking.connection import Connection



class RejectReason(IntEnum):
    """
    Enum containing all reject reasons
    """
    NoConnection: int = 0
    """
    No Connection was established anyway
    """
    AlreadyConnected: int = 1
    """
    A connection between this client and the server already exists
    """
    Pending: int = 2
    """
    The Conneciton is pending
    """
    ServerFull: int = 3
    """
    The server is already full
    """
    Rejected: int = 4
    """
    The connection got rejected from the server
    """
    Custom: int = 5
    """
    Custom Reason. See additional data for details
    """


class DisconnectReason(IntEnum):
    """
    Disconnect Reason
    """
    NeverConnected: int = 0
    """
    A connection was never established in the first place
    """
    ConnectionRejected: int = 1
    """
    The connection got rejected
    """
    TransportError: int = 2
    """
    An Transport-Level error occured
    """
    TimedOut: int = 3
    """
    The connection timed out
    """
    Kicked: int = 4
    """
    The client got kicked from the server
    """
    ServerStopped: int = 5
    """
    The server was stopped
    """
    Disconected: int = 6
    """
    The client requested to be disconencted
    """
    PoorConnection: int = 7

REJECT_REASON_STR = {
    RejectReason.NoConnection: CR_NO_CONNECTION,
    RejectReason.ServerFull: CR_SERVER_FULL,
    RejectReason.Rejected: CR_REJECTED,
    RejectReason.Custom: CR_CUSTOM
}


def rejectReasonToString(rejectReason: Union[RejectReason, int]) -> str:
    """
    :param rejectReason: Reject reason to get
    :return: Human readable reject reason
    """
    if rejectReason in REJECT_REASON_STR:
        return REJECT_REASON_STR[rejectReason]
    return UNKNOWN_REASON


DISCONNECT_REASON_STR = {
    DisconnectReason.NeverConnected: DC_NEVER_CONNECTED,
    DisconnectReason.TransportError: DC_TRANSPORT_ERROR,
    DisconnectReason.TimedOut: DC_TIMED_OUT,
    DisconnectReason.Kicked: DC_KICKED,
    DisconnectReason.ServerStopped: DC_SERVER_STOPPED,
    DisconnectReason.Disconected: DC_DISCONNECTED,
    DisconnectReason.PoorConnection: DC_POOR_CONNECTION
}


def disconnectReasonToString(disconnectReason: Union[DisconnectReason, int]) -> str:
    """
    :param disconnectReason: Disconnect reason to get
    :return: Human readable disconnect reason
    """
    if disconnectReason in DISCONNECT_REASON_STR:
        return DISCONNECT_REASON_STR[disconnectReason]
    return UNKNOWN_REASON


# internal read-only
class MessageToHandle:
    """
    Struct for handling messages
    """
    def __init__(self, message: Message, header: Union["MessageHeader", int], fromConnection: "Connection"):
        self.message: Message = message
        self.header: Union["MessageHeader", int] = header
        self.fromConnection: "Connection" = fromConnection

class HeartbeatEvent(DelayedEvent):
    """
    Heartbeat Event for the priority queue
    """
    def __init__(self, priority, peer):
        super(HeartbeatEvent, self).__init__(priority)
        self.peer = peer

    def __call__(self, *args, **kwargs):
        self.peer.heartbeat()

class Peer:
    """
    Provides base functionality for Server and Client
    """
    def __init__(self, logName: str = "PEER"):
        """
        Initializes the peer
        :param logName:
        """
        super(Peer, self).__init__()
        self._useMessageHandlers: bool = True  # TODO: Implement
        self.__logName = logName

        self._defaultTimeout = 5000

        self.__timeout_time = self._defaultTimeout
        self._connectTimeoutTime = 10000
        self.heartbeat_interval = 1000
        self.current_time = 0
        self.__startTime = time()

        self.messageQueue: List[MessageToHandle] = []
        self.eventQueue: PriorityQueue = PriorityQueue(0)


    @property
    def timeoutTime(self):
        return self.__timeout_time

    @timeoutTime.setter
    def timeoutTime(self, value: int):
        self.__timeout_time = value

    def startTime(self):
        """
        Starts tracking how much time has passed.
        :return:
        """
        self.__startTime = time()

    def stopTime(self):
        """
        Stops tracking how much time has passed.
        :return:
        """
        self.current_time = 0
        self.eventQueue.queue.clear()

    def heartbeat(self):
        """
        Beats the heart.
        :return:
        """
        # Not implemented here
        pass

    def update(self):
        """
        Handles any received messages and invokes any delayed events which need to be invoked.
        :return:
        """
        self.current_time = int((time() - self.__startTime) * 1000)

        while len(self.eventQueue.queue) > 0 and self.eventQueue.queue[0].priority < self.current_time:
            event = self.eventQueue.get()
            event()

    def executeLater(self, delay: int, event: DelayedEvent):
        """
        Sets up a delayed event to be executed after the given time has passed

        :param delay: How long from now to execute the delayed event, in milliseconds.
        :param event: The delayed event to execute later
        :return:
        """
        event.priority = delay + self.current_time
        self.eventQueue.put(event)

    def _handleMessages(self):
        """
        Handles all queued messages
        :return:
        """
        while len(self.messageQueue) > 0:
            msgHandle: MessageToHandle = self.messageQueue.pop()
            self.handle(message=msgHandle.message, header=msgHandle.header, connection=msgHandle.fromConnection)

    def _handleData(self, data: Union[bytes, bytearray, List[int]], amount: int, connection: "Connection"):
        """
        Handles data received by the transport

        :param data:raw data to interpret as message
        :param amount: amount of bytes to read in data
        :param connection: connection the data was received from
        :return:
        """
        header = data[0] & HEADER_BITMASK
        message = createRawMessage(data)
        if message.sendMode == MessageHeader.Notify:
            if amount < MIN_NOTIFY_BYTES:
                return
            connection.processNotify(data, len(data), message)
        elif message.sendMode == MessageHeader.Unreliable:
            self.messageQueue.append(MessageToHandle(message, header, connection))
            connection.metrics.receivedUnreliable(len(data))
        else:
            if amount < MIN_RELIABLE_BYTES:
                return
            if connection.shouldHandle(message.seqID):
                self.messageQueue.append(MessageToHandle(message, header, connection))
            else:
                connection.metrics.incrementReliableDiscarded()

    def handle(self, message: Message, header: Union["MessageHeader", int], connection: "Connection"):
        """
        Handles a message

        :param message: The message to handle
        :param header: The message's header type
        :param connection: The connection which the message was received on
        :return:
        """
        # Not implemented here
        pass

    def disconnect(self, connection: "Connection", reason: Union[DisconnectReason, int]):
        """
        Disconnects the connection in question. Necessary for connections to be able to initiate disconnections (like in the case of poor connection quality).

        :param The connection to disconnect.
        :param The reason why the connection is being disconnected.
        :return:
        """
        pass