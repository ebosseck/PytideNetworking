from enum import IntEnum
from typing import Literal, Union, List

BYTE_ORDER_LITTLE: Literal['big', 'little'] = "little"
BYTE_ORDER_BIG: Literal['big', 'little'] = "big"

class MessageHeader(IntEnum):
    Unreliable: int = 0
    """An unreliable user message"""
    Ack: int = 1
    """An internal unreliable ack message"""
    AckExtra: int = 2
    """An internal unreliable ack message, used when acknowledging a sequence ID other than the last received one"""
    Connect: int = 3
    """An internal unreliable connect message"""
    Reject: int = 4
    """An internal unreliable connection rejection message"""
    Heartbeat: int = 5
    """An internal heartbeat connection rejection message"""
    Disconnect: int = 6
    """An internal unreliable disconnect message"""

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

        self.data: bytearray = bytearray()
        """
        Payload of the message
        """

    def createBytestream(self):
        """
        Assembles the bytes representing this message
        :return: the bytes representing this message
        """
        bytestream: bytearray = bytearray()
        bytestream.append(self.header & 0xff)

        if self.hasSequenceID:
            bytestream += self.seqID.to_bytes(length=2, byteorder=self.byte_order, signed=False)

        if self.hasMessageID:
            bytestream += self.msgID.to_bytes(length=2, byteorder=self.byte_order, signed=False)

        bytestream += self.data

        return bytestream, len(bytestream)

    def createConnectBytes(self):
        """
        Assemble the bytes representing this message sans Header
        :return: the bytes representing this message sans header
        """
        bytestream: bytearray = bytearray()

        if self.hasMessageID:
            bytestream += self.msgID.to_bytes(length=2, byteorder=self.byte_order, signed=False)

        bytestream += self.data

        return bytestream, len(bytestream)

    def fromBytestream(self, bytestream: Union[bytes, bytearray, List[int]], amount: int = -1):
        """
        Populate this message from the given Byte stream

        :param bytestream: Bytes containing the data to populate the message with
        :param amount: Amount of bytes to populate the message with
        :return:
        """
        if amount > 0:
            bytestream = bytestream[: amount]

        self.header = bytestream[0]
        readPos = 1

        if self.hasSequenceID:
            self.seqID = int.from_bytes(bytestream[readPos: readPos+2], self.byte_order, signed=False)
            readPos += 2

        if self.hasMessageID: # only user generated messages
            self.msgID = int.from_bytes(bytestream[readPos: readPos + 2], self.byte_order, signed=False)
            readPos += 2

        self.data = bytestream[readPos:]

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
        return MessageSendMode.Reliable if self.hasSequenceID else MessageSendMode.Unreliable

    def release(self):
        """
        Release this message back into it's pool
        """
        # Not Implemented
        pass

