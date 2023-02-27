from time import time
from enum import IntEnum
from typing import Optional, Dict, Union, List

from pytidenetworking.message_base import MessageBase, MessageSendMode, MessageHeader

from .pending_message import PendingMessage, createAndSend
from .message import createInternal as createMessage, Message

from pytidenetworking.peer import Peer
from pytidenetworking.utils.helper import getSequenceGap
from .utils.logengine import getLogger

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
        self.__id: int = 0
        self.__state = ConnectionState.Connecting
        self.__rtt: int = -1
        self.__smoothRtt: int = 0

        self.__lastHeartbeat: float = 0
        self.__lastPingID: int = 0
        self.__pendingPingId: int = 0
        self.__pendingPingSendTime: float = 0

        self.__canTimeout: bool = True

        self.__pendingMessages: Dict[int, PendingMessage] = {}

        self._peer: Optional[Peer] = None

        self.__lastReceivedSeqID: int = 0
        self.__acksBitfield: int = 0
        self.__duplicateFilterBitfield: int = 0
        self.__lastAckedSeqID: int = 0
        self.__ackedMessagesBitfield: int = 0
        self.__lastSequenceID: int = 0

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
    def hasTimedOut(self):
        """
        :return: True if the connection has timed out
        """
        return self.__canTimeout and (time() - self.__lastHeartbeat) * 1000 > self._peer.timeout_time

    @property
    def hasConnectAttemptTimedOut(self):
        """

        :return: True if the connection attempt has timed out. Uses a multiple of Peer.TimeoutTime
        and ignores the value of CanTimeout
        """
        return (time() - self.__lastHeartbeat) * 1000 > self._peer.timeout_time * 2

    #endregion

    @property
    def pendingMessages(self):
        """
        The currently pending reliably sent messages whose delivery has not been acknowledged yet.
        Stored by sequence ID.
        :return:
        """
        return self.__pendingMessages

    @property
    def peer(self):
        """
        :return: The local peer this connection is associated with.
        """
        return self._peer

#    @peer.setter
#    def peer(self, value):
#        self._peer = value

    @property
    def nextSequenceID(self):
        """

        :return: The next sequence ID to use.
        """
        return (self.__lastSequenceID + 1) & 0xffff # Ushort + simulated overflow

    #endregion

    def resetTimeout(self):
        """
        Resets the connection's timeout time.
        """
        self.__lastHeartbeat = time()

    #region Sending

    def sendMessage(self, message: MessageBase, shouldRelease: bool = True):
        """
        Sends a message.

        :param message: Message to send
        :param shouldRelease: If true, the message is released back into the message pool. Defaults to true
        :return:
        """
        if message.sendMode == MessageSendMode.Unreliable:
            self.send(*message.createBytestream())
        else:
            seqID = self.nextSequenceID
            createAndSend(seqID, message, self)

        if shouldRelease:
            message.release()

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

    #region Ack handling

    def reliableHandle(self, sequenceID: int) -> bool:
        """
        Updates acks and determines whether the message is a duplicate.

        :param sequenceID: The message's sequence ID.
        :return: True if the message should be handled.
        """
        doHandle: bool = True

        sequenceGap: int = getSequenceGap(sequenceID, self.__lastReceivedSeqID)
        if sequenceGap > 0:
            # The received message ID is newer than the previous one
            if sequenceGap > 64:
                logger.warning("The gap between received sequence IDs was very large ({})! If the connection's packet "
                               "loss, latency, or your send rate of reliable messages increases much further, "
                               "sequence IDs may begin falling outside the bounds of the duplicate filter.".format(
                                sequenceGap))

            self.__duplicateFilterBitfield = (self.__duplicateFilterBitfield << sequenceGap) & 0xffff_ffff_ffff_ffff
            if sequenceGap <= 16:
                shiftedBits = (self.__acksBitfield << sequenceGap) & 0xffff_ffff_ffff_ffff
                self.__acksBitfield = shiftedBits & 0xffff
                self.__duplicateFilterBitfield |= shiftedBits >> 16

                doHandle = self.updateAckBitfield(sequenceGap)
                self.__lastReceivedSeqID = sequenceID
            elif sequenceGap <= 80:
                shiftedBits = (self.__acksBitfield << (sequenceGap - 16)) & 0xffff_ffff_ffff_ffff
                self.__acksBitfield = 0 # reset, since all its bits are moved to the duplicate detection
                self.__duplicateFilterBitfield |= shiftedBits

                doHandle = self.updateDuplicateFilterBitfield(sequenceGap)

        elif sequenceGap < 0:
            sequenceGap = -sequenceGap
            if sequenceGap <= 16:
                doHandle = self.updateAckBitfield(sequenceGap)
            elif sequenceGap <= 80:
                doHandle = self.updateDuplicateFilterBitfield(sequenceGap)

        else:
            doHandle = False

        self.sendAck(sequenceID)
        return doHandle

    def updateAckBitfield(self, sequenceGap) -> bool:
        """
        Updates the acks bitfield and determines whether or not to handle the message.

        :param sequenceGap: The gap between the newly received sequence ID and the previously last received sequence ID.
        :return: True if the message should be handled, based on whether or not it's a duplicate.
        """
        seqIDBit = (1 << sequenceGap -1) & 0xffff

        if (self.__acksBitfield & seqIDBit) == 0: # Message is not received before
            self.__acksBitfield |= seqIDBit
            return True
        return False

    def updateDuplicateFilterBitfield(self, sequenceGap) -> bool:
        """
        Updates the duplicate filter bitfield and determines whether or not to handle the message.

        :param sequenceGap: The gap between the newly received sequence ID and the previously last received sequence ID.
        :return: True if the message should be handled, based on if it's a duplicate.
        """
        seqIDBit = (1 << sequenceGap - 1 - 16) & 0xffff_ffff_ffff_ffff

        if (self.__duplicateFilterBitfield & seqIDBit) == 0: # Message is not received before
            self.__duplicateFilterBitfield |= seqIDBit
            return True
        return False

    def updateReceivedAcks(self, remoteLastReceivedSeqID: int, remoteAcksBitField: int):
        """
        Updates which messages we've received acks for.

        :param remoteLastReceivedSeqID: The latest sequence ID that the other end has received.
        :param remoteAcksBitField: A redundant list of sequence IDs that the other end has (or has not) received.
        :return:
        """
        sequenceGap = getSequenceGap(remoteLastReceivedSeqID, self.__lastAckedSeqID)

        if sequenceGap > 0:
            for i in range(1, sequenceGap):
                self.__ackedMessagesBitfield <<= 1
                self.checkMessageAckStatus((self.__lastAckedSeqID - 16 + i) & 0xffff, LEFT_BIT)
            self.__ackedMessagesBitfield <<= 1
            self.__ackedMessagesBitfield |= (remoteAcksBitField | (1 << sequenceGap - 1)) & 0xffff
            self.__lastAckedSeqID = remoteLastReceivedSeqID

            self.checkMessageAckStatus((self.__lastAckedSeqID - 16) & 0xffff, LEFT_BIT)

        elif sequenceGap < 0:
            #TODO: Check if this case ever executes & see if this section remains in C# version long term
            sequenceGap = (-sequenceGap - 1) & 0xffff
            ackedBit = (1 << sequenceGap) & 0xffff

            self.__ackedMessagesBitfield |= ackedBit
            if remoteLastReceivedSeqID in self.__pendingMessages:
                self.__pendingMessages[remoteLastReceivedSeqID].clear()
        else:
            self.__ackedMessagesBitfield |= remoteAcksBitField
            self.checkMessageAckStatus((self.__lastAckedSeqID - 16) & 0xffff, LEFT_BIT)

    def checkMessageAckStatus(self, sequenceID: int, bit: int):
        """
        Check the ack status of the given sequence ID.

        :param sequenceID: The sequence ID whose ack status to check.
        :param bit: The bit corresponding to the sequence ID's position in the bit field.
        :return:
        """
        if (self.__ackedMessagesBitfield & bit) == 0:
            if sequenceID in self.__pendingMessages:
                self.__pendingMessages[sequenceID].retrySend()
        else:
            if sequenceID in self.__pendingMessages:
                self.__pendingMessages[sequenceID].clear()

    def ackMessage(self, seqID: int):
        """
        Immediately marks the PendingMessage of a given sequence ID as delivered.
        :param seqID: The sequence ID that was acknowledged.
        :return:
        """
        if seqID in self.__pendingMessages:
            self.__pendingMessages[seqID].clear()

    #endregion

    def setPending(self):
        """
        Puts the connection in the pending state.
        :return:
        """
        if self.isConnecting:
            self.__state = ConnectionState.Pending
            self.resetTimeout()

    def localDisconnect(self):
        """
        Cleans up the local side of the connection.

        :return:
        """
        self.__state = ConnectionState.NotConnected

        for msg in self.pendingMessages.values():
            msg.clear(False)

        self.pendingMessages.clear()

    #region Messages
    def sendAck(self, sequenceID):
        """
        Sends an ack message for the given sequence ID

        :param sequenceID: The sequence ID to acknowledge
        :return:
        """
        message = createMessage(MessageHeader.Ack if sequenceID == self.__lastReceivedSeqID else MessageHeader.AckExtra)
        message.putUInt16(self.__lastReceivedSeqID)
        message.putUInt16(self.__acksBitfield)

        if (sequenceID != self.__lastReceivedSeqID):
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

        self.ackMessage(remoteLastReceivedSeqID)
        self.updateReceivedAcks(remoteLastReceivedSeqID, remoteAcksBitField)

    def handleAckExtra(self, message: Message):
        """
        Handles an ack message for a sequence ID other than the last received one

        :param message: The ack message to handle
        :return:
        """
        remoteLastReceivedSeqID = message.getUInt16()
        remoteAcksBitField = message.getUInt16()
        ackSeqID = message.getUInt16()

        self.ackMessage(ackSeqID)
        self.updateReceivedAcks(remoteLastReceivedSeqID, remoteAcksBitField)

    #region Server

    def sendWelcome(self):
        """
        Sends a welcome message
        :return:
        """
        message = createMessage(MessageHeader.Welcome)
        message.putUInt16(self.__id)
        self.sendMessage(message)

    def handleWelcomeResponse(self, message: Message):
        """
        Handles a welcome message on the server

        :param message: The welcome message to handle
        :return:
        """
        id = message.getUInt16()

        if self.__id != id:
            logger.error("Client has assumed ID {} instead of {}!".format(id, self.__id))

        self.__state = ConnectionState.Connected
        self.resetTimeout()

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
        message.putInt8(pingID)

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
        self.__pendingPingSendTime = time()

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
            self.rtt = max(1, int((time() - self.__pendingPingSendTime) * 1000))

        self.resetTimeout()
    #endregion

    #endregion

    #region Abstracts
    def receive(self):
        """Polls the socket and checks if any data was received."""
        # Not implemented
        pass
    #endregion