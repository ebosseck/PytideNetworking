# Updated to 2.1.0

from enum import IntEnum
from math import ceil
from typing import Union, List, Tuple
from .utils.converter import BITS_PER_BYTE, BITS_PER_SEGMENT, ushortToBits, setBits64, toVarULong, ensureSpaceAvailable, \
    setBitsFromBytes, ushortFromBits, getBits, fromVarULong, bytesFromBits

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

BYTE_ORDER_LITTLE: Literal['big', 'little'] = "little"
BYTE_ORDER_BIG: Literal['big', 'little'] = "big"

HEADER_BITS = 4
HEADER_BITMASK = (1 << HEADER_BITS) - 1
UNRELIABLE_HEADER_BITS = HEADER_BITS
RELIABLE_HEADER_BITS = HEADER_BITS + 2 * BITS_PER_BYTE
NOTIFY_HEADER_BITS = HEADER_BITS + 5 * BITS_PER_BYTE
MIN_UNRELIABLE_BYTES = ceil(UNRELIABLE_HEADER_BITS / BITS_PER_BYTE)
MIN_RELIABLE_BYTES = ceil(RELIABLE_HEADER_BITS / BITS_PER_BYTE)
MIN_NOTIFY_BYTES = ceil(NOTIFY_HEADER_BITS / BITS_PER_BYTE)

MAX_HEADER_SIZE = NOTIFY_HEADER_BITS
_MAX_SIZE = ceil(MAX_HEADER_SIZE / BITS_PER_BYTE) + 1225
INSTANCES_PER_PEER = 4

_MAX_BIT_COUNT = _MAX_SIZE * BITS_PER_BYTE
_MAX_ARRAY_SIZE = ceil(_MAX_SIZE / BITS_PER_SEGMENT)

class MessageHeader(IntEnum):
    Unreliable: int = 0
    """An unreliable user message"""
    Ack: int = 1
    """An internal unreliable ack message"""
    Connect: int = 2
    """An internal unreliable connect message"""
    Reject: int = 3
    """An internal unreliable connection rejection message"""
    Heartbeat: int = 4
    """An internal heartbeat connection rejection message"""
    Disconnect: int = 5
    """An internal unreliable disconnect message"""

    Notify: int = 6
    """A notify message."""

    Reliable: int = 7
    """A reliable user message"""
    Welcome: int = 8
    """An internal reliable welcome message"""
    ClientConnected: int = 9
    """An internal reliable client connected message"""
    ClientDisconnected: int = 10
    """An internal reliable client disconnected message"""

class MessageSendMode(IntEnum):
    Unreliable = MessageHeader.Unreliable
    """Unreliable send mode"""
    Notify = MessageHeader.Notify
    """Guarantees order but not delivery. Notifies the sender of what happened via the Connection.NotifyDelivered and 
    Connection.NotifyLost events. The receiver must handle notify messages via the Connection.NotifyReceived event,
    which is different from the other two send modes."""
    Reliable = MessageHeader.Reliable
    """Reliable send mode"""

class MessageBase:
    """
    Base class for Messages and Pending Messages
    """
    def __init__(self):
        """
        Initialize a new base message
        """

        self.byte_order: Literal['big', 'little'] = BYTE_ORDER_LITTLE
        """
        Byte order to use for this message
        """

        self.header: int = -1
        """
        Header value of the message
        """
        self.seqID: int = -1
        """
        Sequence ID of the message if applicable
        """
        self.msgID: int = -1
        """
        Message ID of the message if applicable
        """
        self.notifyBits: int = -1
        """
        Bit sequence of the notify bits
        """

        self.data: bytearray = bytearray()
        """
        Payload of the message
        """

        self.readBit = 0
        self.writeBit = 0

    @property
    def bytesAvailable(self):
        """
        :return: the number of bytes still available within the message
        """
        return _MAX_SIZE - len(self.data)

    @property
    def readBits(self):
        return self.readBit

    @property
    def unreadBits(self):
        return self.writeBit - self.readBit

    @property
    def writtenBits(self):
        return self.writeBit

    @property
    def unwrittenBits(self):
        return _MAX_BIT_COUNT - self.writeBit

    @property
    def bytesInUse(self):
        return ceil(self.writeBit / BITS_PER_BYTE)

    def setNotifyBits(self, notify_bits: int):
        self.notifyBits = notify_bits

    def createBytestream(self):
        """
        Assembles the bytes representing this message
        :return: the bytes representing this message
        """
        bytestream: bytearray = bytearray()

        if self.header < MessageHeader.Notify:
            # Unreliable
            bytestream, bitpos = self.__makeHeaderUnreliable(bytestream)
        elif self.header < MessageHeader.Reliable:
            # Notify
            bytestream, bitpos = self.__makeHeaderNotify(bytestream)
        else:
            #Reliable
            bytestream, bitpos = self.__makeHeaderReliable(bytestream)

        if self.hasMessageID:
            msgIDBytes = toVarULong(self.msgID)
            bytestream = ensureSpaceAvailable(bytestream, bitpos, len(msgIDBytes) * BITS_PER_BYTE)
            bytestream = setBitsFromBytes(msgIDBytes, len(msgIDBytes) * BITS_PER_BYTE, bytestream, bitpos)
            bitpos += len(msgIDBytes) * BITS_PER_BYTE

        bytestream = setBitsFromBytes(self.data, self.writeBit, bytestream, bitpos)
        return bytestream, len(bytestream)

    def __makeHeaderUnreliable(self, bytestream: Union[bytearray, List[int]]) -> Tuple[Union[bytearray, List[int]], int]:
        bytes_missing = 1 - len(bytestream)
        if bytes_missing > 0:
            bytestream.extend([0] * bytes_missing)
        bytestream[0] = self.header

        return bytestream, 4

    def __makeHeaderReliable(self, bytestream: Union[bytearray, List[int]]) -> Tuple[Union[bytearray, List[int]], int]:
        bytes_missing = 3 - len(bytestream)
        if bytes_missing > 0:
            bytestream.extend([0] * bytes_missing)

        bytestream[0] = self.header
        bytestream = ushortToBits(self.seqID, bytestream, 4)

        return bytestream, 20

    def __makeHeaderNotify(self, bytestream: Union[bytearray, List[int]]) -> Tuple[Union[bytearray, List[int]], int]:
        bytes_missing = 6 - len(bytestream)
        if bytes_missing > 0:
            bytestream.extend([0] * bytes_missing)

        bytestream[0] = self.header
        bytestream = setBits64(self.notifyBits, 40, bytestream, 4)

        return bytestream, 44
    def createConnectBytes(self):
        """
        Assemble the bytes representing this message sans Header
        :return: the bytes representing this message sans header
        """
        bytestream: bytearray = bytearray()

        bitpos = 0
        if self.hasMessageID:
            msgIDBytes = toVarULong(self.msgID)
            bytestream = ensureSpaceAvailable(bytestream, 0, len(msgIDBytes) * BITS_PER_BYTE)
            bytestream = setBitsFromBytes(msgIDBytes, len(msgIDBytes) * BITS_PER_BYTE, bytestream, 0)
            bitpos = len(msgIDBytes) * BITS_PER_BYTE

        bytestream = setBitsFromBytes(self.data, self.writeBit, bytestream, bitpos)

        return bytestream, len(bytestream)

    def fromBytestream(self, bytestream: Union[bytes, bytearray, List[int]], amount: int = -1):
        """
        Populate this message from the given Byte stream

        :param bytestream: Bytes containing the data to populate the message with
        :param amount: Amount of bytes to populate the message with
        :return:
        """
        #if amount > 0:
            #bytestream = bytestream[: amount]

        self.header = bytestream[0] & HEADER_BITMASK
        if self.header < MessageHeader.Notify:
            # Unreliable
            bitpos = self.__readHeaderUnreliable(bytestream)
        elif self.header < MessageHeader.Reliable:
            # Notify
            bitpos = self.__readHeaderNotify(bytestream)
        else:
            #Reliable
            bitpos = self.__readHeaderReliable(bytestream)

        if self.hasMessageID: # only user generated messages
            self.msgID, readbits = fromVarULong(bytestream, bitpos)
            bitpos += readbits

        self.data = bytesFromBits(bytestream, (len(bytestream) * BITS_PER_BYTE) - bitpos, bitpos)

        self.readBit = 0
        self.writeBit = 0

    def __str__(self):
        return '\n'.join([
            "Header: {}".format(self.header),
            "ReadPos: {}".format(self.readBit),
            "WritePos: {}".format(self.writeBit),
            "Payload: {}".format(self.data)
        ])

    def __readHeaderUnreliable(self, bytestream: Union[bytearray, List[int]]) -> int:
        # No further content in header
        return 4

    def __readHeaderReliable(self, bytestream: Union[bytearray, List[int]]) -> int:
        self.seqID = ushortFromBits(bytestream, 4)
        return 20

    def __readHeaderNotify(self, bytestream: Union[bytearray, List[int]]) -> int:
        self.notifyBits = getBits(40, bytestream, 4)
        return 44

    @property
    def hasSequenceID(self):
        """
        :return: True if the message type has a sequence ID in its header (i.e. header byte >= 7)
        """
        return self.header >= MessageHeader.Reliable

    @property
    def hasMessageID(self):
        """
        :return: True if this message type has a message ID in its header (i.e. header byte == 0 or 7)
        """
        if self.header == MessageHeader.Unreliable or self.header == MessageHeader.Reliable:
            return True
        return False

    @property
    def sendMode(self):
        """
        :return: the send mode of this message (either Reliable = 7 or Unreliable = 0)
        """
        if self.header < MessageHeader.Notify:
            return MessageSendMode.Unreliable
        elif self.header < MessageHeader.Reliable:
            return MessageSendMode.Notify
        else:
            return MessageSendMode.Reliable

    def release(self):
        """
        Release this message back into it's pool
        """
        # Not Implemented
        pass

    def putBits(self, notify_bits, param, HEADER_BITS):
        pass

