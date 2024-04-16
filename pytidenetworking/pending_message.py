# Updated to 2.1.0

from typing import TYPE_CHECKING

from pytidenetworking.message_base import MessageBase
from pytidenetworking.peer import DisconnectReason
from pytidenetworking.utils.delayed_events import DelayedEvent
from pytidenetworking.utils.logengine import getLogger
from pytidenetworking.utils.object_pool import ObjectPool

if TYPE_CHECKING:
    from pytidenetworking.connection import Connection

PENDING_MESSAGE_POOL_SIZE = 10
PENDING_MESSAGE_POOL = ObjectPool(PENDING_MESSAGE_POOL_SIZE)

RETRY_TIME_MULTIPLIER = 1.2
MAX_SEND_ATTEMPTS = 15

logger = getLogger("pytide.PendingMessage")

class PendingMessageResendEvent(DelayedEvent):
    """
    Resends a PendingMessage when invoked.
    """
    def __init__(self, priority, message):
        super(PendingMessageResendEvent, self).__init__(priority)
        self.message = message

    def __call__(self, *args, **kwargs):
        if self.priority == self.message.lastSendTime: # check if message was already resent
            self.message.retrySend()

class PendingMessage(MessageBase):
    """
    Represents a currently pending reliably sent message whose delivery has not been acknowledged yet.
    """
    def __init__(self, connection: "Connection" = None):
        """
        Constructor

        :param connection: Connection used to send & resend the pending message
        """
        super(PendingMessage, self).__init__()
        self.__lastSendTime: int = 0
        """
        The time of the latest send attempt
        """
        self.connection: "Connection" = connection
        """
        The Connection to use to send (and resend) the pending message
        """

        self.__sendAttempts: int = 0
        """
        How many send attempts have been made so far.
        """
        self.__wasCleared: bool = False
        """
        Whether the pending message has been cleared or not.
        """

    @property
    def lastSendTime(self):
        """
        The time of the latest send attempt
        """
        return self.__lastSendTime

    def release(self):
        """
        Releases the message back into the pool
        :return:
        """
        PENDING_MESSAGE_POOL.release(self)

    def retrySend(self):
        """
        Resends the message.
        :return:
        """
        if not self.__wasCleared:
            peerTime = self.connection.peer.current_time
            if self.__lastSendTime + (25 if self.connection.smoothRTT < 0 else self.connection.smoothRTT / 2) <= peerTime:
                self.trySend()
            else:
                delay = 50 if self.connection.smoothRTT < 0 else max(10,
                                                            int(self.connection.smoothRTT * RETRY_TIME_MULTIPLIER))
                self.connection.peer.executeLater(delay, PendingMessageResendEvent(priority=delay, message=self))

    def trySend(self):
        """
        Attempts to send the message.
        :return:
        """
        if self.__sendAttempts >= MAX_SEND_ATTEMPTS and self.connection.canQualityDisconnect:
            self.clear()
            self.connection.peer.disconnect(connection=self.connection, reason=DisconnectReason.PoorConnection)
            return
        bytestream, amount = self.createBytestream()
        self.connection.send(bytestream, amount)
        self.connection.metrics.sentReliable(amount)
        self.__lastSendTime = self.connection.peer.current_time
        self.__sendAttempts += 1

        delay = 50 if self.connection.smoothRTT < 0 else max(10,
                                                               int(self.connection.smoothRTT * RETRY_TIME_MULTIPLIER))
        self.connection.peer.executeLater(delay, PendingMessageResendEvent(priority=delay, message=self))

    def clear(self):
        """
        Clears the message.

        :param shouldRemoveFromDictionary: Whether or not to remove the message from the connection's pending messages
        :return:
        """
        self.__wasCleared = True
        self.release()


def createPending(sequenceID: int, message: MessageBase, connection: "Connection"):
    """
    Retrieves a PendingMessage instance, initializes it and then sends it.

    :param sequenceID: The sequence ID of the message
    :param message: The message that is being sent reliably
    :param connection: The Connection to use to send (and resend) the pending message.
    :return: the pending message set up
    """
    pendingMessage: PendingMessage = PENDING_MESSAGE_POOL.acquire()
    pendingMessage.connection = connection

    pendingMessage.header = message.header
    pendingMessage.seqID = sequenceID
    pendingMessage.msgID = message.msgID
    pendingMessage.data = message.data

    pendingMessage.readBit = message.readBit
    pendingMessage.writeBit = message.writeBit

    pendingMessage.__sendAttempts = 0
    pendingMessage.__wasCleared = False

    return pendingMessage

def createPendingMessage():
    """
    Factory method for object pool
    :return: a new instance of Pending Message
    """
    return PendingMessage()

PENDING_MESSAGE_POOL.createObject = createPendingMessage