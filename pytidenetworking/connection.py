# Updated to 2.1.0

from time import time
from enum import IntEnum
from typing import Optional, Dict, Union, List

from pytidenetworking.message_base import MessageBase, MessageSendMode, MessageHeader, HEADER_BITS

from .pending_message import PendingMessage, createPending
from .message import createInternal as createMessage, Message

from pytidenetworking.peer import Peer, DisconnectReason
from .utils.bitfield import Bitfield
from .utils.connection_metrics import ConnectionMetrics
from .utils.converter import ushortFromBits, byteFromBits
from .utils.eventhandler import EventHandler
from .utils.logengine import getLogger
from .utils.notify_sequencer import NotifySequencer
from .utils.relieble_sequencer import ReliableSequencer

LEFT_BIT = 0b1000_0000_0000_0000

logger = getLogger("pytide.connection")

class ConnectionState(IntEnum):
    """
    The state of a connection
    """
    NotConnected = 0
    """
    Not connected. No connection has been established or the connection has been closed.
    """
    Connecting = 1
    """
    Connecting. Still trying to establish a connection.
    """
    Pending = 2
    """
    Connection is pending. The server is still determining whether or not the connection should be allowed.
    """
    Connected = 3
    """
    Connected. A connection has been established successfully.
    """

class Connection:
    """
    Represents a connection to a server or client
    """
    def __init__(self):
        """
        Initializes the connection.
        """

        self.notifyDelivered = EventHandler()
        """
        Invoked when the notify message with the given sequence ID is successfully delivered.
        """
        self.notifyLost = EventHandler()
        """
        Invoked when the notify message with the given sequence ID is lost.
        """
        self.notifyReceived = EventHandler()
        """
        Invoked when a notify message is received.
        """
        self.reliableDelivered = EventHandler()
        """
        Invoked when the reliable message with the given sequence ID is successfully delivered.
        """

        self.__id: int = 0
        self.__state = ConnectionState.Connecting
        self.__rtt: int = -1
        self.__smoothRtt: int = -1

        self.timeoutTime = 0

        self.__lastHeartbeat: int = 0
        self.__lastPingID: int = 0
        self.__pendingPingId: int = 0
        self.__pendingPingSendTime: int = 0

        self.__canTimeout: bool = True
        self.__connectionMetrics: ConnectionMetrics = ConnectionMetrics()
        self.canQualityDisconnect = True

        self.maxAvgSendAttempts: int = 5
        self.avgSendAttemptsResilience: int = 64
        self.maxSendAttempts: int = 15
        self.maxNotifyLoss: float = 0.05
        self.notifyLossResilience: int = 64

        self.__notify: NotifySequencer = NotifySequencer(self)
        self.__reliable: ReliableSequencer = ReliableSequencer(self)

        self.__pendingMessages: Dict[int, PendingMessage] = {}

        self._peer: Optional[Peer] = None

        self.__sendAttemptViolations: int = 0
        self.__lossRateViolations: int = 0

    #region Properties
    @property
    def id(self) -> int:
        """
        The Connections numeric ID
        :return:
        """
        return self.__id

    @id.setter
    def id(self, value):
        """
        The Connections numeric ID
        :param value: value to set
        :return:
        """
        self.__id = value

    #region Connection State
    @property
    def isNotConnected(self) -> bool:
        """
        :return: True if the connection is currently not connected nor trying to connect.
        """
        return self.__state == ConnectionState.NotConnected

    @property
    def isConnecting(self) -> bool:
        """
        :return: True if the client is currently in the process of connecting
        """
        return self.__state == ConnectionState.Connecting

    @property
    def isPending(self) -> bool:
        """
        :return: True if the client's connection is currently pending (will only be True when a server doesn't
        immediately accept the connection request)
        """
        return self.__state == ConnectionState.Pending

    @property
    def isConnected(self) -> bool:
        """
        :return: True if the client is currently connected.
        """
        return self.__state == ConnectionState.Connected
    #endregion

    #region RTT
    @property
    def rtt(self) -> int:
        """
        The round trip time (ping) of the connection, in milliseconds. -1 if not calculated yet.
        """
        return self.__rtt

    @rtt.setter
    def rtt(self, value: int):
        """
        The round trip time (ping) of the connection, in milliseconds. -1 if not calculated yet.
        """
        self.__smoothRtt = value if self.__rtt < 0 else max(1.0, self.__smoothRtt * .7 + value * .3)
        self.__rtt = value

    @property
    def smoothRTT(self) -> int:
        """
        The smoothed round trip time (ping) of the connection, in milliseconds. -1 if not calculated yet.

        This value is slower to accurately represent lasting changes in latency than rtt, but it is less susceptible to
        changing drastically due to significant—but temporary—jumps in latency.

        :return:
        """
        return int(self.__smoothRtt)

    #endregion

    #region Timeout
    @property
    def canTimeout(self):
        """
        :return: True
        """
        return self.__canTimeout

    @canTimeout.setter
    def canTimeout(self, value):
        """
        Set if the connection can time out.
        :param value:
        :return:
        """
        if value:
            self.resetTimeout()
        self.__canTimeout = value

    @property
    def metrics(self) -> ConnectionMetrics:
        return self.__connectionMetrics

    @property
    def hasTimedOut(self):
        """
        :return: True if the connection has timed out
        """
        return self.__canTimeout and (self._peer.current_time - self.__lastHeartbeat) > self.timeoutTime

    @property
    def hasConnectAttemptTimedOut(self):
        """

        :return: True if the connection attempt has timed out. Uses a multiple of Peer.TimeoutTime
        and ignores the value of CanTimeout
        """
        return self.__canTimeout and (self._peer.current_time - self.__lastHeartbeat) > self._peer._connectTimeoutTime

    #endregion

 #   @property
 #   def pendingMessages(self):
 #       """
 #       The currently pending reliably sent messages whose delivery has not been acknowledged yet.
 #       Stored by sequence ID.
 #       :return:
 #       """
 #       return self.__pendingMessages

    @property
    def peer(self):
        """
        :return: The local peer this connection is associated with.
        """
        return self._peer

#    @peer.setter - Private in 2.1.0
#    def peer(self, value):
#        self._peer = value

    #endregion

    def initialize(self, peer: Peer, timeoutTime: int):
        self._peer = peer
        self.timeoutTime = timeoutTime

    def resetTimeout(self):
        """
        Resets the connection's timeout time.
        """
        self.__lastHeartbeat = time()

    #region Sending

    def sendMessage(self, message: MessageBase, shouldRelease: bool = True) -> int:
        """
        Sends a message.

        :param message: Message to send
        :param shouldRelease: If true, the message is released back into the message pool. Defaults to true
        :return: the sequence ID of the message
        """
        sequenceID: int = 0
        if message.sendMode == MessageSendMode.Notify:
            sequenceID = self.__notify.insertHeader(message)
            byteAmount = message.bytesInUse
            self.send(*message.createBytestream())
            self.__connectionMetrics.sentNotify(byteAmount)
        elif message.sendMode == MessageSendMode.Unreliable:
            byteAmount = message.bytesInUse
            self.send(*message.createBytestream())
            self.__connectionMetrics.sentUnreliable(byteAmount)
        else:
            sequenceID = self.__reliable.nextSequenceID
            pendingMessage = createPending(sequenceID, message, self)
            self.__pendingMessages[sequenceID] = pendingMessage
            pendingMessage.trySend()
            self.__connectionMetrics.incrementReliableUniques()

        if shouldRelease:
            message.release()

        return sequenceID

    def send(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int):
        """
        Sends data
        :param dataBuffer: The buffer containing the data
        :param amount: The number of bytes in the array which should be sent
        :return:
        """
        # Not Implemented (only in subclasses)
        pass

    #endregion

    #region Notify Handling

    def processNotify(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int, message: MessageBase):
        self.__notify.updateReceivedAcks(ushortFromBits(dataBuffer, HEADER_BITS), byteFromBits(dataBuffer, HEADER_BITS + 16))
        self.__connectionMetrics.receivedNotify(amount)
        if self.__notify.shouldHandle(ushortFromBits(dataBuffer, HEADER_BITS + 24)):
            self.notifyReceived(message)
        else:
            self.__connectionMetrics.incrementNotifyDiscarded()
    #endregion

    #region reliable handling

    def shouldHandle(self, sequenceID) -> bool:
        return self.__reliable.shouldHandle(sequenceID)

    #endregion

    def localDisconnect(self):
        """
        Cleans up the local side of the connection.

        :return:
        """
        self.__state = ConnectionState.NotConnected

        for msg in self.__pendingMessages.values():
            msg.clear()

        self.__pendingMessages.clear()

    def resendMessage(self, sequenceID: int):
        """
        Resend the pending message with the given sequence ID
        :param: sequenceID - Sequence ID of the message
        """
        if sequenceID in self.__pendingMessages:
            self.__pendingMessages[sequenceID].retrySend()

    def clearMessage(self, sequenceID: int):
        if sequenceID in self.__pendingMessages:
            self.reliableDelivered(sequenceID)
            self.__pendingMessages[sequenceID].clear()
            del self.__pendingMessages[sequenceID]
            self.__updateSendAttemptViolations()

    def setPending(self):
        if self.isConnecting:
            self.__state = ConnectionState.Pending
            self.resetTimeout()

    def __updateSendAttemptViolations(self):
        if self.__connectionMetrics.rollingReliableSends.mean > self.maxAvgSendAttempts:
            self.__sendAttemptViolations += 1
            if self.__sendAttemptViolations >= self.avgSendAttemptsResilience:
                self._peer.disconnect(self, DisconnectReason.PoorConnection)
        else:
            self.__sendAttemptViolations = 0

    def __updateLossViolations(self):
        if self.__connectionMetrics.rollingNotifyLossRate > self.maxNotifyLoss:
            self.__lossRateViolations += 1
            if self.__lossRateViolations >= self.notifyLossResilience:
                self._peer.disconnect(self, DisconnectReason.PoorConnection)
        else:
            self.__lossRateViolations = 0

    #region Messages
    def sendAck(self, sequenceID: int, lastReceivedSeqID: int, receivedSeqIds: Bitfield):
        """
        Sends an ack message for the given sequence ID

        :param sequenceID: The sequence ID to acknowledge
        :return:
        """
        message = createMessage(MessageHeader.Ack)
        message.putUInt16(lastReceivedSeqID)
        message.putUInt16(receivedSeqIds.first16)

        if (sequenceID == lastReceivedSeqID):
            message.putBool(False)
        else:
            message.putBool(True)
            message.putUInt16(sequenceID)

        self.sendMessage(message)

    def handleAck(self, message: Message):
        """
        Handles an ack message

        :param message: The ack message to handle
        :return:
        """
        remoteLastReceivedSeqID = message.getUInt16()
        remoteAcksBitField = message.getUInt16()
        getFromMsg = message.getBool()
        ackedSeqID = message.getUInt16() if getFromMsg else remoteLastReceivedSeqID

        self.clearMessage(ackedSeqID)
        self.__reliable.updateReceivedAcks(remoteLastReceivedSeqID, remoteAcksBitField)

    #region Server

    def sendWelcome(self):
        """
        Sends a welcome message
        :return:
        """
        message = createMessage(MessageHeader.Welcome)
        message.putUInt16(self.__id)
        self.sendMessage(message)

    def handleWelcomeResponse(self, message: Message) -> bool:
        """
        Handles a welcome message on the server

        :param message: The welcome message to handle
        :return:
        """
        if not self.isPending:
            return False

        id = message.getUInt16()

        if self.__id != id:
            logger.error("Client has assumed ID {} instead of {}!".format(id, self.__id))

        self.__state = ConnectionState.Connected
        self.resetTimeout()
        return True

    def handleHeartbeat(self, message: Message):
        """
        Handles a heartbeat message

        :param message: The heartbeat message to handle
        :return:
        """
        self.respondHeartbeat(message.getUInt8())
        self.rtt = message.getUInt16()

        self.resetTimeout()

    def respondHeartbeat(self, pingID: int):
        """
        ends a heartbeat message

        :param pingID: ping ID of the heartbeat to send
        :return:
        """
        message = createMessage(MessageHeader.Heartbeat)
        message.putUInt8(pingID)

        self.sendMessage(message)

    #endregion

    #region Client

    def handleWelcome(self, message: Message):
        """
        Handles a welcome message on the client

        :param message: The welcome message to handle
        :return:
        """
        self.__id = message.getUInt16()
        self.__state = ConnectionState.Connected
        self.resetTimeout()

        self.respondWelcome()

    def respondWelcome(self):
        """
        Sends a welcome response message

        :return:
        """
        message = createMessage(MessageHeader.Welcome)
        message.putUInt16(self.__id)

        self.sendMessage(message)

    def sendHeartbeat(self):
        """
        Sends a heartbeat message.

        :return:
        """
        self.__pendingPingId = self.__lastPingID+1
        self.__pendingPingSendTime = self._peer.current_time

        message = createMessage(MessageHeader.Heartbeat)
        message.putInt8(self.__pendingPingId)
        message.putUInt16(self.rtt if self.rtt >= 0 else 0)

        self.sendMessage(message)

    def handleHeartbeatResponse(self, message: Message):
        """
        Handles a heartbeat message

        :param message: The heartbeat message to handle
        :return:
        """
        pingID = message.getUInt8()

        if self.__pendingPingId == pingID:
            self.rtt = max(1, self._peer.current_time - self.__pendingPingSendTime)

        self.resetTimeout()
    #endregion

    #region Events

    def onNotifyDelivered(self, sequenceID: int):
        self.__connectionMetrics.deliveredNotify()
        self.notifyDelivered(sequenceID)
        self.__updateLossViolations()

    def onNotifyLost(self, sequenceID: int):
        self.__connectionMetrics.lostNotify()
        self.notifyLost(sequenceID)
        self.__updateLossViolations()

    #endregion

    #endregion

    #region Abstracts
    def receive(self):
        """Polls the socket and checks if any data was received."""
        # Not implemented
        pass
    #endregion
