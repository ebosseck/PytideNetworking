from typing import List, Literal, Union

from .message_base import MessageBase, MessageHeader, MessageSendMode
from .utils.converter import fp32_to_bytes, fp64_to_bytes, bytes_to_fp32, bytes_to_fp64
from .utils.exceptions import InsufficientCapacityException, ArgumentOutOfRangeException, NotEnoughBytesError
from .utils.logengine import getLogger

from .constants import activeCount

from enum import IntEnum
from math import ceil

from .utils.object_pool import ObjectPool


logger = getLogger("pytide.Message")

#region Static Vars

POOL_SIZE = 10

MAX_HEADER_SIZE = 5
_MAX_SIZE = 1225 + MAX_HEADER_SIZE
INSTANCES_PER_PEER = 4

MESSAGE_POOL: ObjectPool['Message'] = ObjectPool(POOL_SIZE)

@property
def maxSize():
    """
    :return: the maximum message size allowed
    """
    return _MAX_SIZE

@property
def maxPayloadSize():
    """
    :return: the maximal payload size allowed for messages
    """
    return _MAX_SIZE - MAX_HEADER_SIZE

@maxPayloadSize.setter
def maxPayloadSize(value):
    """
    Sets the maximum message payload size

    :param value: new maximal payload size
    :return:
    """
    global _MAX_SIZE
    if activeCount() > 0:
        logger.error("Changing the max message size is not allowed while a Server or Client is running!")
    else:
        if value < 0:
            logger.error(
                "The max payload size cannot be negative! Setting it to 0 instead of the given value ({}).".format(
                    value))
            _MAX_SIZE = MAX_HEADER_SIZE
        else:
            _MAX_SIZE = MAX_HEADER_SIZE + value
        MESSAGE_POOL.clearPool()


#endregion


class Message(MessageBase):
    """
    Class representing a Message
    """

    def __init__(self):
        """
        Constructor for the message
        """
        super(Message, self).__init__()
        self.readPos = 0

    @property
    def bytesAvailable(self):
        """
        :return: the number of bytes still available within the message
        """
        return _MAX_SIZE - len(self.data)

    def prepareForUse(self, header: Union[MessageSendMode, MessageHeader] = None):
        """
        Prepares the message for reuse

        :param header: Header to set for the new use of the message object
        :return:
        """
        self.readPos = 0
        self.data = bytearray()
        if header is not None:
            self.header = header

    def release(self):
        """
        Release this object back into the message pool
        :return:
        """
        MESSAGE_POOL.release(self)

    #region tools

    def appendData(self, value: bytes):
        """
        Appends the given data to the message body
        :param value: data to append
        """
        self.data.extend(value)

    def replaceData(self, value: bytes, pos: int):
        """
        Writes the given data at the given position of the message body

        :param value: bytes to write to the messages payload
        :param pos: position to write the data to
        """
        if len(self.data) < pos:
            self.data.extend([0] * (pos - len(self.data)))

        for idx in range(len(value)):
            if pos < len(self.data):
                self.data[pos + idx] = value[idx]
            else:
                self.data.extend(value[idx:])
                return

    #endregion

    #region Checks

    def checkAvailable(self, required):
        """
        Checks if the requested number of bytes is still available

        :param required: the number of bytes required to be available
        :raises: InsufficientCapacityException if not enough bytes are available
        """
        if self.bytesAvailable < required:
            raise InsufficientCapacityException()

    def checkReadAvailable(self, readpos: int, expectedBytes: int):
        """
        Checks if the required amount of bytes is available for reading
        :param readpos: Position to start reading from
        :param expectedBytes: Number of bytes expected available for reading
        :raises: NotEnoughBytesError if not enough bytes are available
        """
        if len(self.data) - readpos < expectedBytes:
            raise NotEnoughBytesError()

    def computeReadPointer(self, pos: int) -> int:
        """
        Computes the new read position from the given position

        :param pos: position to check
        :return: pos if pos >= 0, the read pointer of this message otherwise
        """
        if pos < 0:
            return self.readPos
        return pos

    #endregion


    # region Getter & Putter

    #region Bytes

    def putBytes(self, value: Union[bytes, bytearray, List[int]], pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        if value is None:
            return 0
        if pos < 0:
            self.appendData(value)
        else:
            self.replaceData(value, pos)

        return len(value)

    def getBytes(self, length: int, pos: int = -1):
        """
        Gets the substring of bytes at the given position of the given length

        :param length: length of the bytestring requested
        :param pos: starting position of the byte string requested
        :return: the requested bytestring
        """
        pos = self.computeReadPointer(pos)

        self.checkReadAvailable(pos, length)

        self.readPos = pos+length

        return self.data[pos: pos+length]

    #endregion

    #region Boolean

    def putBool(self, value: bool, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(1)
        if value is None:
            value = 0
        if pos < 0:
            self.data.append(0x01 if value else 0x00)
        else:
            self.data[pos] = 0x01 if value else 0x00
        return 1

    def getBool(self, pos: int = -1) -> bool:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
        defaults to the next value in the message
        :return: the value at this position
        """
        return self.getBytes(1, pos)[0] != 0x00

    def putBoolArray(self, value: List[bool], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        isMultipleOf8 = len(value) % 8 == 0
        byteLength = ceil(len(value) / 8.0)

        self.checkAvailable(byteLength)

        for i in range(byteLength):
            nextByte = 0
            bitsToWrite = 8
            if i+1 == byteLength and not isMultipleOf8:
                bitsToWrite = len(value) % 8

            for bit in range(bitsToWrite):
                nextByte = nextByte | ((1 if value[i*8 + bit] else 0) << bit)

            if pos < 0:
                self.appendData((nextByte & 0xff).to_bytes(length=1, byteorder=self.byte_order, signed=False))
            else:
                self.replaceData((nextByte & 0xff).to_bytes(length=1, byteorder=self.byte_order, signed=False), pos + bytesWritten)
            bytesWritten += 1

        return bytesWritten

    def getBoolArray(self, length:int = -1, pos:int = -1) -> List[bool]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length
        isLengthMultipleOf8 = length % 8 == 0
        byteAmount = ceil(length / 8.0)

        self.checkReadAvailable(self.readPos, byteAmount)

        result = []
        for i in range(byteAmount):
            bitsToRead = 8
            if (i+1) == byteAmount and not isLengthMultipleOf8:
                bitsToRead = length % 8

            currentByte = self.getInt8()
            for bit in range(bitsToRead):
                result.append(((currentByte >> bit) & 0x01) == 1)
        return result

    #endregion

    #region Byte

    def putInt8(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(1)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=1, byteorder=self.byte_order, signed=True))
        else:
            self.replaceData(value.to_bytes(length=1, byteorder=self.byte_order, signed=True), pos)
        return 1

    def getInt8(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(1, pos), self.byte_order, signed=True)

    def putInt8Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value))
        for val in value:
            if pos < 0:
                self.appendData(val.to_bytes(1, self.byte_order, signed=True))
            else:
                self.replaceData(val.to_bytes(1, self.byte_order, signed=True), pos + bytesWritten)

        return bytesWritten + len(value)

    def getInt8Array(self,  length:int = -1, pos:int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getInt8())

        return result

    def putUInt8(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(1)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=1, byteorder=self.byte_order, signed=False))
        else:
            self.replaceData(value.to_bytes(length=1, byteorder=self.byte_order, signed=False), pos)
        return 1

    def getUInt8(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(1, pos), self.byte_order, signed=False)

    def putUInt8Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value))
        for val in value:
            if pos < 0:
                self.appendData(val.to_bytes(length=1, byteorder=self.byte_order, signed=False))
            else:
                self.replaceData(val.to_bytes(length=1, byteorder=self.byte_order, signed=False), pos + bytesWritten)

        return bytesWritten + len(value)

    def getUInt8Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getUInt8())

        return result

    #endregion

    #region Short

    def putInt16(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(2)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=2, byteorder=self.byte_order, signed=True))
        else:
            self.replaceData(value.to_bytes(length=2, byteorder=self.byte_order, signed=True), pos)
        return 2

    def getInt16(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(2, pos), self.byte_order, signed=True)

    def putInt16Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 2)

        for val in value:
            bytesWritten += self.putInt16(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getInt16Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 2*length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getInt16())

        return result

    def putUInt16(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(2)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=2, byteorder=self.byte_order, signed=False))
        else:
            self.replaceData(value.to_bytes(length=2, byteorder=self.byte_order, signed=False), pos)
        return 2

    def getUInt16(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(2, pos), self.byte_order, signed=False)

    def putUInt16Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 2)

        for val in value:
            bytesWritten += self.putUInt16(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getUInt16Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 2*length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getUInt16())

        return result

    #endregion

    #region Int

    def putInt32(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(4)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=4, byteorder=self.byte_order, signed=True))
        else:
            self.replaceData(value.to_bytes(length=4, byteorder=self.byte_order, signed=True), pos)
        return 4

    def getInt32(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(4, pos), self.byte_order, signed=True)

    def getInt32Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 4* length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getInt32())

        return result

    def putInt32Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 4)

        for val in value:
            bytesWritten += self.putInt32(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def putUInt32(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(4)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=4, byteorder=self.byte_order, signed=False))
        else:
            self.replaceData(value.to_bytes(length=4, byteorder=self.byte_order, signed=False), pos)
        return 4

    def getUInt32(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(4, pos), self.byte_order, signed=False)

    def putUInt32Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 4)

        for val in value:
            bytesWritten += self.putUInt32(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getUInt32Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 4 * length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getUInt32())

        return result


    #endregion

    #region Long

    def putInt64(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(8)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=8, byteorder=self.byte_order, signed=True))
        else:
            self.replaceData(value.to_bytes(length=8, byteorder=self.byte_order, signed=True), pos)
        return 8

    def getInt64(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(8, pos), self.byte_order, signed=True)

    def putInt64Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 8)

        for val in value:
            bytesWritten += self.putInt64(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getInt64Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 8 * length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getInt64())

        return result

    def putUInt64(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(8)
        if value is None:
            value = 0
        if pos < 0:
            self.appendData(value.to_bytes(length=8, byteorder=self.byte_order, signed=False))
        else:
            self.replaceData(value.to_bytes(length=8, byteorder=self.byte_order, signed=False), pos)
        return 8

    def getUInt64(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(8, pos), self.byte_order, signed=False)

    def putUInt64Array(self, value: List[int], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 8)

        for val in value:
            bytesWritten += self.putUInt64(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getUInt64Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 8 * length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getUInt64())

        return result

    #endregion

    #region Float

    def putFloat(self, value: float, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(4)
        if value is None:
            value = float("nan")
        if pos < 0:
            self.appendData(fp32_to_bytes(value))
        else:
            self.replaceData(fp32_to_bytes(value), pos)
        return 4

    def getFloat(self, pos: int = -1) -> float:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return bytes_to_fp32(self.getBytes(4, pos))

    def putFloatArray(self, value: List[float], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 4)

        for val in value:
            bytesWritten += self.putFloat(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getFloatArray(self, length: int = -1, pos: int = -1) -> List[float]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 4* length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getFloat())

        return result

    #endregion

    #region Double

    def putDouble(self, value: float, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkAvailable(8)
        if value is None:
            value = float("nan")
        if pos < 0:
            self.appendData(fp64_to_bytes(value))
        else:
            self.replaceData(fp64_to_bytes(value), pos)
        return 8

    def getDouble(self, pos: int = -1) -> float:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return bytes_to_fp64(self.getBytes(8, pos))

    def putDoubleArray(self, value: List[float], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        self.checkAvailable(len(value) * 8)

        for val in value:
            bytesWritten += self.putDouble(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getDoubleArray(self, length: int = -1, pos: int = -1) -> List[float]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.checkReadAvailable(self.readPos, 4* length)

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getDouble())

        return result

    #endregion

    #region String

    def putString(self, value: str, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        encoded = value.encode("utf-8")
        offset = self.putArrayLength(len(encoded), pos)

        self.checkAvailable(len(encoded))
        if pos < 0:
            self.appendData(encoded)
        else:
            self.replaceData(encoded, offset+pos)
        return len(encoded) + offset

    def getString(self, pos: int = -1) -> str:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """

        length = self.readArrayLength(pos)

        if pos < 0:
            pos = self.readPos
        else:
            if length < 127:
                pos += 1
            else:
                pos += 2

        self.readPos = pos+length
        return self.data[pos: pos+length].decode("utf-8")

    def putStringArray(self, value: List[str], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bytesWritten = 0
        if includeLength:
            bytesWritten = self.putArrayLength(len(value), pos)

        for val in value:
            bytesWritten += self.putString(val, -1 if pos < 0 else pos+bytesWritten)

        return bytesWritten

    def getStringArray(self, length: int = -1, pos: int = -1) -> List[str]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length = self.readArrayLength(pos) if length < 0 else length

        self.readPos = self.computeReadPointer(pos)
        result = []
        for _ in range(length):
            result.append(self.getString())

        return result

    #endregion

    # region Aliases for Int

    addByte = putUInt8
    addSByte = putInt8
    addByteArray = putUInt8Array
    addSByteArray = putInt8Array

    getByte = getUInt8
    getSByte = getInt8
    getByteArray = getUInt8Array
    getSByteArray = getInt8Array

    addShort = putInt16
    addUShort = putUInt16
    addShortArray = putInt16Array
    addUShortArray = putUInt16Array

    getShort = getInt16
    getUShort = getUInt16
    getShortArray = getInt16Array
    getUShortArray = getUInt16Array

    addInt = putInt32
    addUInt = putUInt32
    addIntArray = putInt32Array
    addUIntArray = putUInt32Array

    getInt = getInt32
    getUInt = getUInt32
    getIntArray = getInt32Array
    getUIntArray = getUInt32Array

    addLong = putInt64
    addULong = putUInt64
    addLongArray = putInt64Array
    addULongArray = putUInt64Array

    getLong = getInt64
    getULong = getUInt64
    getLongArray = getInt64Array
    getULongArray = getUInt64Array

    addFloat = putFloat
    addFloatArray = putFloatArray

    addDouble = putDouble
    addDoubleArray = putDoubleArray

    addString = putString
    addStringArray = putStringArray
    # endregion

    #region Array Length

    def putArrayLength(self, length, pos = -1):
        """
        Writes the given length in array length format

        :param length: length to write
        :param pos: position to write the length to, -1 to append
        :return: number of bytes written
        """
        if self.bytesAvailable < 1:
            raise InsufficientCapacityException()

        if length <= 0b0111_1111:
            if pos < 0:
                self.appendData((length&0xff).to_bytes(1, "little", signed=False))
            else:
                self.replaceData((length&0xff).to_bytes(1, "little", signed=False), pos)
            return 1
        else:
            if length > 0b0111_1111_1111_1111:
                raise ArgumentOutOfRangeException()
            if self.bytesAvailable < 2:
                raise InsufficientCapacityException()
            length |= 0b_1000_0000_0000_0000
            if pos < 0:
                self.appendData(((length>>8)&0xff).to_bytes(1, "little", signed=False))
                self.appendData((length & 0xff).to_bytes(1, "little", signed=False))
            else:
                self.replaceData(((length >> 8) & 0xff).to_bytes(1, "little", signed=False), pos)
                self.replaceData((length & 0xff).to_bytes(1, "little", signed=False), pos + 1)
            return 2

    def readArrayLength(self, pos = -1) -> int:
        """
        Reads an Array Length value at the specified position
        :param pos: Position to read from (defaults to < 0 = Automatic)
        :return:
        """
        self.readPos = self.readPos if pos < 0 else pos

        self.checkReadAvailable(self.readPos, 1)
        firstByte = self.getInt8(self.readPos)

        if (firstByte & 0b1000_0000) == 0:
            return firstByte

        self.checkReadAvailable(self.readPos, 1)
        return ((firstByte << 8) | self.getInt8(self.readPos)) & 0b0111_1111_1111_1111

    #endregion

    #endregion


#region Creator

def create(sendMode: Union[MessageSendMode, int], id: int):
    """
    Prepare a new custom message

    :param sendMode: Send mode of the message (Reliable or Unreliable)
    :param id: ID of the message
    :return: the prepared message
    """
    msg = MESSAGE_POOL.acquire()
    msg.prepareForUse(sendMode)
    msg.msgID = id
    return msg


def createInternal(header: Union[MessageHeader, int] = None):
    """
    Prepare a new custom message

    :param header: Header of the message (defaults to None)
    :return: the prepared message
    """
    msg = MESSAGE_POOL.acquire()
    msg.prepareForUse(header)
    return msg


def createFromBytes(data: Union[bytes, bytearray, List[int]], amount: int = -1):
    """
    Creates a new message from raw bytes
    :param data: raw bytes to interpret as message
    :param amount: Number of bytes to interpret as message
    :return: the message created from the given bytes
    """
    message = MESSAGE_POOL.acquire()
    message.prepareForUse()
    message.fromBytestream(data, amount=amount)

    return message
#endregion


def __createMessageObject() -> Message:
    """
    Factory for Object Pool
    :return: a newly created Message object
    """
    return Message()


MESSAGE_POOL.createObject = __createMessageObject
