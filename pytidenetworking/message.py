# Updated to 2.1.0

try:
    from typing import Literal, Optional
except ImportError:
    from typing_extensions import Literal, Optional

from .message_base import *
from .utils.converter import fp32_to_bytes, fp64_to_bytes, bytes_to_fp32, bytes_to_fp64, BITS_PER_BYTE, \
    BITS_PER_SEGMENT, bytesToBits, bytesFromBits, setBitsFromBytes, getBitsToBytes, setBits8, getBits
from .utils.exceptions import InsufficientCapacityException, ArgumentOutOfRangeException, NotEnoughBytesError
from .utils.logengine import getLogger

from .constants import activeCount

from math import ceil

from .utils.object_pool import ObjectPool

logger = getLogger("pytide.Message")

#region Static Vars

POOL_SIZE = 10



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
    return _MAX_SIZE - ceil(MAX_HEADER_SIZE / BITS_PER_BYTE)

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

        else:
            _MAX_SIZE = ceil(MAX_HEADER_SIZE / BITS_PER_BYTE) + value
            _MAX_BIT_COUNT = _MAX_SIZE * BITS_PER_BYTE
            _MAX_ARRAY_SIZE = ceil(_MAX_SIZE / BITS_PER_SEGMENT)
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


    def init(self, header: Union[MessageSendMode, MessageHeader] = None):
        """
        Prepares the message for reuse

        :param header: Header to set for the new use of the message object
        :return:
        """
        self.data = bytearray()
        if header is not None:
            self.header = header
        self.readBit = 0
        self.writeBit = 0

    def release(self):
        """
        Release this object back into the message pool
        :return:
        """
        MESSAGE_POOL.release(self)

    #region tools

    # def appendData(self, value: bytes):
    #     """
    #     Appends the given data to the message body
    #     :param value: data to append
    #     """
    #     self.data.extend(value)
    #
    # def replaceData(self, value: bytes, pos: int):
    #     """
    #     Writes the given data at the given position of the message body
    #
    #     :param value: bytes to write to the messages payload
    #     :param pos: position to write the data to
    #     """
    #     if len(self.data) < pos:
    #         self.data.extend([0] * (pos - len(self.data)))
    #
    #     for idx in range(len(value)):
    #         if pos < len(self.data):
    #             self.data[pos + idx] = value[idx]
    #         else:
    #             self.data.extend(value[idx:])
    #             return

    def appendBits(self, value: bytes):
        """
        Appends the given data to the message body
        :param value: data to append
        """
        requiredLength = ceil(float(self.writeBit) / BITS_PER_BYTE) + (len(value))
        if len(self.data) < requiredLength:
            self.data.extend([0] * ((requiredLength) - len(self.data)))
        self.data = bytesToBits(value, self.data, self.writeBit)
        self.writeBit += len(value) * BITS_PER_BYTE

    def replaceBits(self, value: bytes, bitpos: int):
        """
        Writes the given data at the given position of the message body

        :param value: bytes to write to the messages payload
        :param bitpos: position to write the data to
        """
        requiredLength = ceil(bitpos / BITS_PER_BYTE) + (len(value))
        if len(self.data) < requiredLength:
            self.data.extend([0] * (requiredLength - len(self.data)))
            self.writeBit = max(self.writeBit, requiredLength)
        self.data = bytesToBits(value, self.data, bitpos)


    #endregion

    #region Checks

#    def checkAvailable(self, required):
#        """
#        Checks if the requested number of bytes is still available
#
#        :param required: the number of bytes required to be available
#        :raises: InsufficientCapacityException if not enough bytes are available
#        """
#        if self.bytesAvailable < required:
#            raise InsufficientCapacityException()

    def checkBitsAvailable(self, required):
        """
        Checks if the requested number of bits is still available

        :param required: the number of bytes required to be available
        :raises: InsufficientCapacityException if not enough bytes are available
        """
        if self.unwrittenBits < required:
            raise InsufficientCapacityException()

    #def checkReadAvailable(self, readpos: int, expectedBytes: int):
    #    """
    #    Checks if the required amount of bytes is available for reading
    #    :param readpos: Position to start reading from
    #    :param expectedBytes: Number of bytes expected available for reading
    #    :raises: NotEnoughBytesError if not enough bytes are available
    #    """
    #    if len(self.data) - readpos < expectedBytes:
    #        raise NotEnoughBytesError()

    def checkReadBitsAvailable(self, readpos: int, expectedBits: int):
        """
        Checks if the required amount of bbits is available for reading
        :param readpos: Position to start reading from in bits
        :param expectedBits: Number of bits expected available for reading
        :raises: NotEnoughBytesError if not enough bytes are available
        """
        if ((len(self.data)) * BITS_PER_BYTE) - readpos < expectedBits:
            raise NotEnoughBytesError()


#    def computeReadPointer(self, pos: int) -> int:
#        """
#        Computes the new read position from the given position
#
#        :param pos: position to check
#        :return: pos if pos >= 0, the read pointer of this message otherwise
#        """
#        if pos < 0:
#            return self.readPos
#        return pos

    def computeReadPointerBits(self, pos: int) -> int:
        """
        Computes the new read position from the given position

        :param pos: position to check
        :return: pos if pos >= 0, the read pointer of this message otherwise
        """
        if pos < 0:
            return self.readBits
        return pos

    #endregion


    #region Getter & Putter

    #region Bits

    def putBits(self, bits: Union[int, bytes, bytearray, List[int]], amount: int, pos: int = -1):
        if isinstance(bits, int):
            bits = bits.to_bytes(ceil(amount/8), self.byte_order)

        if pos < 0:
            self.data = setBitsFromBytes(bits, amount, self.data, self.writeBit)
            self.writeBit += amount
        else:
            self.data = setBitsFromBytes(bits, amount, self.data, pos)

    def peekBits(self, amount: int, startBit: int=-1):
        if startBit < 0:
            startBit = self.readBit

        return getBitsToBytes(self.data, amount, startBit)

    def getBits(self, amount: int, startBit: int = -1):
        if startBit < 0:
            bits = self.peekBits(amount, startBit)
            self.readBit += amount
        else:
            bits = self.peekBits(amount, startBit)
        return bits
    #endregion

    #region Variable Length

    def putVarULong(self, value: int, pos: int = -1) -> int:
        #tmp_data = []
        #while True:
        #    byte_val = value & 0b_0111_1111
        #    value >>= 7
        #    if value != 0:
        #        byte_val |= 0b_0111_1111
        #        tmp_data.append(byte_val)
        #    else:
        #        tmp_data.append(byte_val)
        #        break
        return self.putBytes(toVarULong(value), pos)

    def getVarULong(self, pos: int):
        #shift = 0
        #val = 0
        #bytes_read = 0
        #while True:
        #    bytes_read += 1
        #    byte_val = self.getUInt8(pos)
        #    val |= (byte_val & 0b0111_1111) << shift
        #    shift += 7
        #    if byte_val & 0b1000_0000 == 1:
        #       break
        pos = self.computeReadPointerBits(pos)
        return fromVarULong(self.data, pos)

    #endregion

    #region Constant Width

    #region Bytes

    def putBytes(self, value: Union[bytes, bytearray, List[int]], pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the messages payload
        :param pos: in bits: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bits written to the messages payload
        """
        if value is None:
            return 0
        if pos < 0:
            self.appendBits(value)
        else:
            self.replaceBits(value, pos)

        return len(value) * BITS_PER_BYTE

    def getBytes(self, length: int, pos: int = -1):
        """
        Gets the substring of bytes at the given position of the given length

        :param length: length of the bytestring requested IN BYTES
        :param pos: starting position of the byte string requested
        :return: the requested bytestring
        """
        pos = self.computeReadPointerBits(pos)
        self.checkReadBitsAvailable(pos, length * BITS_PER_BYTE)

        self.readBit = pos + (length * BITS_PER_BYTE)

        return bytesFromBits(self.data, length * BITS_PER_BYTE, pos)#self.data[pos: pos+length]

    #endregion

    #region Boolean

    def putBool(self, value: bool, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bits written to the messages payload
        """
        self.checkBitsAvailable(1)
        if value is None:
            value = 0

        if pos < 0:
            setBits8(0x01 if value else 0x00, 1, self.data, self.writeBit)
            self.writeBit += 1
        else:
            setBits8(0x01 if value else 0x00, 1, self.data, pos)
        return 1

    def getBool(self, pos: int = -1) -> bool:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
        defaults to the next value in the message
        :return: the value at this position
        """
        if pos < 0:
            val = getBits(1, self.data, self.readBit) != 0
            self.readBit += 1
            return val
        else:
            return getBits(1, self.data, pos) != 0

    def putBoolArray(self, value: List[bool], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bitfield = bytearray(ceil(len(value) / BITS_PER_BYTE))
        for i in range(len(value)):
            if value[i]:
                byte = i // BITS_PER_BYTE
                bit = i % BITS_PER_BYTE
                bitfield[byte] |= 1 << bit
        writePos = pos
        if pos < 0:
            writePos = self.writeBit

        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), writePos)

        setBitsFromBytes(bitfield, len(value), self.data, writePos+bitsWritten)

        return bitsWritten + len(value)

    def getBoolArray(self, length:int = -1, pos:int = -1) -> List[bool]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        bitpos = self.computeReadPointerBits(pos)
        length, bits_read = self.getVarULong(bitpos) if length < 0 else (length, 0)
        self.checkReadBitsAvailable(bitpos, length)
        result = []
        bitfield = getBitsToBytes(self.data, length, bitpos+bits_read)
        for i in range(length):
            byte = i // BITS_PER_BYTE
            bit = i % BITS_PER_BYTE
            result.append(bitfield[byte] & (1 << bit) != 0)
        if pos < 0:
            self.readBit += bits_read + length
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
        self.checkBitsAvailable(BITS_PER_BYTE)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=1, byteorder=self.byte_order, signed=True))
        else:
            self.replaceBits(value.to_bytes(length=1, byteorder=self.byte_order, signed=True), pos)
        return 1

    def getInt8(self, pos: int = -1) -> int:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """
        return int.from_bytes(self.getBytes(1, pos), self.byte_order, signed=True)

    def putInt8Array(self, value: Union[bytes, bytearray, List[int]], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value)*BITS_PER_BYTE)
        for val in value:
            if pos < 0:
                self.appendBits(val.to_bytes(1, self.byte_order, signed=True))
            else:
                self.replaceBits(val.to_bytes(1, self.byte_order, signed=True), pos + bitsWritten)
            bitsWritten += BITS_PER_BYTE

        return bitsWritten

    def getInt8Array(self,  length:int = -1, pos:int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(BITS_PER_BYTE)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=1, byteorder=self.byte_order, signed=False))
        else:
            self.replaceBits(value.to_bytes(length=1, byteorder=self.byte_order, signed=False), pos)
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
            bytesWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value)*BITS_PER_BYTE)
        for val in value:
            if pos < 0:
                self.appendBits(val.to_bytes(length=1, byteorder=self.byte_order, signed=False))
            else:
                self.replaceBits(val.to_bytes(length=1, byteorder=self.byte_order, signed=False), pos + bytesWritten)

        return bytesWritten + len(value)

    def getUInt8Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(16)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=2, byteorder=self.byte_order, signed=True))
        else:
            self.replaceBits(value.to_bytes(length=2, byteorder=self.byte_order, signed=True), pos)
        return 2 * BITS_PER_BYTE

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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 16)

        for val in value:
            bitsWritten += self.putInt16(val, -1 if pos < 0 else pos+bitsWritten)

        return bitsWritten

    def getInt16Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 2)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(16)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=2, byteorder=self.byte_order, signed=False))
        else:
            self.replaceBits(value.to_bytes(length=2, byteorder=self.byte_order, signed=False), pos)
        return 2 * BITS_PER_BYTE

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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 16)

        for val in value:
            bitsWritten += self.putUInt16(val, -1 if pos < 0 else pos+bitsWritten)

        return bitsWritten

    def getUInt16Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 2)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(32)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=4, byteorder=self.byte_order, signed=True))
        else:
            self.replaceBits(value.to_bytes(length=4, byteorder=self.byte_order, signed=True), pos)
        return 4 * BITS_PER_BYTE

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
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 4)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 16)

        for val in value:
            bitsWritten += self.putInt32(val, -1 if pos < 0 else pos + bitsWritten)

        return bitsWritten

    def putUInt32(self, value: int, pos: int = -1) -> int:
        """
        Puts the given value into the messages payload
        :param value: value to add to the messages payload
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        self.checkBitsAvailable(32)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=4, byteorder=self.byte_order, signed=False))
        else:
            self.replaceBits(value.to_bytes(length=4, byteorder=self.byte_order, signed=False), pos)
        return 4 * BITS_PER_BYTE

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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 32)

        for val in value:
            bitsWritten += self.putUInt32(val, -1 if pos < 0 else pos + bitsWritten)

        return bitsWritten

    def getUInt32Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 4)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(64)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=8, byteorder=self.byte_order, signed=True))
        else:
            self.replaceBits(value.to_bytes(length=8, byteorder=self.byte_order, signed=True), pos)
        return 8 * BITS_PER_BYTE

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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 64)

        for val in value:
            bitsWritten += self.putInt64(val, -1 if pos < 0 else pos + bitsWritten)

        return bitsWritten

    def getInt64Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 8)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(64)
        if value is None:
            value = 0
        if pos < 0:
            self.appendBits(value.to_bytes(length=8, byteorder=self.byte_order, signed=False))
        else:
            self.replaceBits(value.to_bytes(length=8, byteorder=self.byte_order, signed=False), pos)
        return 8 * BITS_PER_BYTE

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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 64)

        for val in value:
            bitsWritten += self.putUInt64(val, -1 if pos < 0 else pos+bitsWritten)

        return bitsWritten

    def getUInt64Array(self, length: int = -1, pos: int = -1) -> List[int]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 8)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(32)
        if value is None:
            value = float("nan")
        if pos < 0:
            self.appendBits(fp32_to_bytes(value))
        else:
            self.replaceBits(fp32_to_bytes(value), pos)
        return 4 * BITS_PER_BYTE

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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 32)

        for val in value:
            bitsWritten += self.putFloat(val, -1 if pos < 0 else pos + bitsWritten)

        return bitsWritten

    def getFloatArray(self, length: int = -1, pos: int = -1) -> List[float]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 4)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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
        self.checkBitsAvailable(64)
        if value is None:
            value = float("nan")
        if pos < 0:
            self.appendBits(fp64_to_bytes(value))
        else:
            self.replaceBits(fp64_to_bytes(value), pos)
        return 8*BITS_PER_BYTE

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
        bitsWritten = 0
        if includeLength:
            bitsWritten = self.putVarULong(len(value), pos)

        self.checkBitsAvailable(len(value) * 64)

        for val in value:
            bitsWritten += self.putDouble(val, -1 if pos < 0 else pos + bitsWritten)

        return bitsWritten

    def getDoubleArray(self, length: int = -1, pos: int = -1) -> List[float]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.checkReadBitsAvailable(self.readBit + bits_read, length * BITS_PER_BYTE * 8)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
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

        return self.putInt8Array(encoded, includeLength=True, pos=pos)

    def getString(self, pos: int = -1) -> str:
        """
        Returns the value at the given position of the message
        :param pos: optional position of the value (if negative: read next value).
         defaults to the next value in the message
        :return: the value at this position
        """

        length, bits_read = self.getVarULong(pos)

        if pos < 0:
            pos = self.readBit

        return self.getBytes(length, pos + bits_read).decode("utf-8")

    def putStringArray(self, value: List[str], includeLength:bool = True, pos: int = -1):
        """
        Puts the given value into the messages payload

        :param value: value to add to the message's payload
        :param includeLength: if True, include the length of the array into the message
        :param pos: overrides the data at the given position if >= 0, otherwise the data is appended
        :return: the number of bytes written to the messages payload
        """
        bits_written = 0
        if includeLength:
            bits_written = self.putVarULong(len(value), pos)

        for val in value:
            bits_written += self.putString(val, -1 if pos < 0 else pos+bits_written)

        return bits_written

    def getStringArray(self, length: int = -1, pos: int = -1) -> List[str]:
        """
        Reads the array of the given length from the given position

        :param length: length of the array to read (defaults to < 0 = Automatic)
        :param pos: position within the message of the array to read (defaults to < 0 = Automatic)
        :return: the Array at the given psoition within the message
        """
        length, bits_read = self.getVarULong(pos) if length < 0 else (length, 0)

        self.readBit = self.computeReadPointerBits(pos) + bits_read
        result = []
        for _ in range(length):
            result.append(self.getString())

        return result

    def appendMessage(self, message: 'Message', amount: Optional[int]=None, startBit: Optional[int]=None):
        if amount is None:
            amount = message.unreadBits
        if startBit is None:
            startBit = message.readBit

        self.checkBitsAvailable(amount)
        self.putBits(message.peekBits(amount, startBit), amount)


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
    msg.init(sendMode)
    msg.msgID = id
    return msg


def createInternal(header: Union[MessageHeader, int] = None):
    """
    Prepare a new custom message

    :param header: Header of the message (defaults to None)
    :return: the prepared message
    """
    msg = MESSAGE_POOL.acquire()
    msg.init(header)
    return msg


def createFromBytes(data: Union[bytes, bytearray, List[int]], amount: int = -1):
    """
    Creates a new message from raw bytes
    :param data: raw bytes to interpret as message
    :param amount: Number of bytes to interpret as message
    :return: the message created from the given bytes
    """
    message = MESSAGE_POOL.acquire()
    message.init()
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
