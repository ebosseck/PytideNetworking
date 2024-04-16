# Updated to 2.1.0

import struct
from math import ceil
from typing import List, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

READABLE_ARRAY = Union[bytes, bytearray, List[int]]
WRITEABLE_ARRAY = Union[bytearray, List[int]]

FLOAT_LITTLE = "<f"
DOUBLE_LITTLE = "<d"

FLOAT_BIG = ">f"
DOUBLE_BIG = ">d"

BITS_PER_BYTE = 8
BITS_PER_SEGMENT = 8 * BITS_PER_BYTE


#region ZigZag Encoding

def zigzagEncode(value: int, bitcount: int):
    """
    Zig-Zag encode the given number of bits from value
    :param value: Value to encode
    :param bitcount: number of bits to encode

    :returns: the encoded value
    """
    return (value >> (bitcount-1)) ^ (value << 1)


def zigzagEncode32(value: int):
    """
    Zig-Zag encode 32 bits from value
    :param value: Value to encode

    :returns: the encoded value
    """
    return zigzagEncode(value, 32)


def zigzagEncode64(value: int):
    """
    Zig-Zag encode 64 bits from value
    :param value: Value to encode

    :returns: the encoded value
    """
    return zigzagEncode(value, 64)


def zigzagDecode(value: int):
    """
    Zigzag decode the given value
    """
    return (value >> 1) ^ -(value&1)

#endregion


#region bits

def ensureSpaceAvailable(bytestream: WRITEABLE_ARRAY, bitpos: int, amount: int):
    bytes_missing = ceil((bitpos + amount) / BITS_PER_BYTE) - len(bytestream)
    if bytes_missing > 0:
        bytestream.extend([0] * bytes_missing)
    return bytestream


#region setBit
def setBits(bitfield: int, amount: int, array: WRITEABLE_ARRAY, startBit: int):
    if amount <= 8:
        return setBits8(bitfield, amount, array, startBit)
    elif amount <= 16:
        return setBits16(bitfield, amount, array, startBit)
    elif amount <= 32:
        return setBits32(bitfield, amount, array, startBit)
    elif amount <= 64:
        return setBits64(bitfield, amount, array, startBit)


def setBits8(bitfield: int, amount: int, array: WRITEABLE_ARRAY, startBit: int):
    mask = ((1<<amount) - 1)&0xff
    bitfield &= mask
    invMask = ~mask
    pos = startBit // BITS_PER_BYTE
    bit = startBit % BITS_PER_BYTE

    ensureSpaceAvailable(array, startBit, 8)

    if bit == 0:
        array[pos] = (bitfield | (array[pos] & invMask)) &0xff
    else:
        array[pos] = ((bitfield << bit) | (array[pos] & ~(mask << bit))) & 0xff
        array[pos+1] = ((bitfield >> (8-bit)) | (array[pos + 1] & (invMask >> (8-bit)))) & 0xff
    return array


def setBits16(bitfield: int, amount: int, array: WRITEABLE_ARRAY, startBit: int):
    mask = ((1 << amount) - 1) & 0xffff
    bitfield &= mask
    invMask = ~mask
    pos = startBit // BITS_PER_BYTE
    bit = startBit % BITS_PER_BYTE

    ensureSpaceAvailable(array, startBit, 16)

    if bit == 0:
        array[pos] = (bitfield | (array[pos] & invMask)) &0xff
        array[pos+1] = (bitfield >> 8 | (array[pos+1] & (invMask >> 8))) & 0xff
    else:
        array[pos] = ((bitfield << bit) | (array[pos] & ~(mask << bit))) & 0xff
        bitfield >>= 8 - bit
        invMask >>= 8 - bit
        array[pos + 1] = (bitfield | (array[pos+1] & invMask)) & 0xff
        array[pos + 2] = ((bitfield >> 8) | (array[pos + 2] & (invMask >> 8))) & 0xff
    return array


def setBits32(bitfield: int, amount: int, array: WRITEABLE_ARRAY, startBit: int):
    mask = ((1 << amount) - 1) & 0xffffffff
    bitfield &= mask
    invMask = ~mask
    pos = startBit // BITS_PER_BYTE
    bit = startBit % BITS_PER_BYTE

    ensureSpaceAvailable(array, startBit, 32)

    if bit == 0:
        array[pos] = (bitfield | (array[pos] & invMask)) & 0xff
        array[pos + 1] = (bitfield >> 8 | (array[pos + 1] & invMask >> 8)) & 0xff
        array[pos + 2] = (bitfield >> 16 | (array[pos + 2] & invMask >> 16)) & 0xff
        array[pos + 3] = (bitfield >> 24 | (array[pos + 3] & invMask >> 24)) & 0xff
    else:
        array[pos] = ((bitfield << bit) | (array[pos] & ~(mask << bit))) & 0xff
        bitfield >>= 8 - bit
        invMask >>= 8 - bit
        array[pos + 1] = (bitfield | (array[pos + 1] & invMask)) & 0xff
        array[pos + 2] = ((bitfield >> 8) | (array[pos + 2] & (invMask >> 8))) & 0xff
        array[pos + 3] = ((bitfield >> 16) | (array[pos + 3] & (invMask >> 16))) & 0xff
        array[pos + 4] = ((bitfield >> 24) | (array[pos + 4] & (invMask >> 24))) & 0xff
    return array


def setBits64(bitfield: int, amount: int, array: WRITEABLE_ARRAY, startBit: int):
    mask = ((1 << amount) - 1) & 0xffffffffffffffff
    bitfield &= mask
    invMask = ~mask
    pos = startBit // BITS_PER_BYTE
    bit = startBit % BITS_PER_BYTE

    ensureSpaceAvailable(array, startBit, 64)

    if bit == 0:
        array[pos] = (bitfield | (array[pos] & invMask)) & 0xff
        array[pos + 1] = (bitfield >> 8 | (array[pos + 1] & invMask >> 8)) & 0xff
        array[pos + 2] = (bitfield >> 16 | (array[pos + 2] & invMask >> 16)) & 0xff
        array[pos + 3] = (bitfield >> 24 | (array[pos + 3] & invMask >> 24)) & 0xff
        array[pos + 4] = (bitfield >> 32 | (array[pos + 4] & invMask >> 32)) & 0xff
        array[pos + 5] = (bitfield >> 40 | (array[pos + 5] & invMask >> 40)) & 0xff
        array[pos + 6] = (bitfield >> 48 | (array[pos + 6] & invMask >> 48)) & 0xff
        array[pos + 7] = (bitfield >> 56 | (array[pos + 7] & invMask >> 56)) & 0xff
    else:
        array[pos] = ((bitfield << bit) | (array[pos] & ~(mask << bit))) & 0xff
        bitfield >>= 8 - bit
        invMask >>= 8 - bit
        array[pos + 1] = (bitfield | (array[pos + 1] & invMask)) & 0xff
        array[pos + 2] = ((bitfield >> 8) | (array[pos + 2] & (invMask >> 8))) & 0xff
        array[pos + 3] = ((bitfield >> 16) | (array[pos + 3] & (invMask >> 16))) & 0xff
        array[pos + 4] = ((bitfield >> 24) | (array[pos + 4] & (invMask >> 24))) & 0xff
        array[pos + 5] = ((bitfield >> 32) | (array[pos + 5] & (invMask >> 32))) & 0xff
        array[pos + 6] = ((bitfield >> 40) | (array[pos + 6] & (invMask >> 40))) & 0xff
        array[pos + 7] = ((bitfield >> 48) | (array[pos + 7] & (invMask >> 48))) & 0xff
        array[pos + 8] = ((bitfield >> 56) | (array[pos + 8] & (invMask >> 56))) & 0xff
    return array


def setBitsFromBytes(bitfield: READABLE_ARRAY, amount: int, array: WRITEABLE_ARRAY, startBit: int):
    pos: int = startBit // BITS_PER_BYTE
    bitoffset: int = startBit % BITS_PER_BYTE
    byte_count = amount // BITS_PER_BYTE
    bits_remaining = amount % BITS_PER_BYTE

    ensureSpaceAvailable(array, startBit, amount)

    if bitoffset == 0:
        for i in range(byte_count):
            array[pos + i] = (bitfield[i]) & 0xff
    else:
        for i in range(byte_count):
            array[pos + i] = ((array[pos + i] & (0xff >> (8 - bitoffset))) | (bitfield[i] << bitoffset)) & 0xff
            array[pos + i + 1] = ((array[pos + i + 1] & (0xff << bitoffset)) | (bitfield[i] >> (8 - bitoffset))) & 0xff

    if bits_remaining != 0:
        bmask = (1 << bits_remaining) - 1

        if bits_remaining + bitoffset <= 8:
            amask = ((0xff >> (8 - bitoffset)) | (0xff << (bitoffset + bits_remaining))) & 0xff
            array[pos + byte_count] = ((array[pos + byte_count] & amask) | ((bitfield[byte_count] & bmask) << bitoffset)) & 0xff
        else:
            array[pos + byte_count] = ((array[pos + byte_count] & (0xff >> (8 - bitoffset))) | ((bitfield[byte_count] & bmask) << bitoffset)) & 0xff
            array[pos + byte_count + 1] = ((array[pos + byte_count + 1] & (0xff << ((bitoffset + bits_remaining) - 8))) | ((bitfield[byte_count] & bmask) >> (8 - bitoffset))) & 0xff

    return array


def setBitsSegmentArray(bitfield: int, amount: int, array: List[int], startBit: int):
    mask = (1 << (amount-1) << 1) - 1
    bitfield &= mask
    pos = startBit // BITS_PER_SEGMENT
    bit = startBit % BITS_PER_SEGMENT

    if bit == 0:
        if len(array) <= pos:
            array.extend([0] * (pos - len(array)))
        array[pos] = bitfield | array[pos] & ~mask
    elif bit + amount < BITS_PER_SEGMENT:
        if len(array) <= pos:
            array.extend([0] * (pos - len(array)))
        array[pos] = (bitfield << bit) | (array[pos] & ~(mask << bit))
    else:
        if len(array) <= (pos+1):
            array.extend([0] * ((pos+1) - len(array)))
        array[pos] = (bitfield << bit) | (array[pos] & ~(mask << bit))
        array[pos + 1] = (bitfield >> (BITS_PER_SEGMENT - bit)) | (array[pos + 1] & ~(mask >> (BITS_PER_SEGMENT - bit)))
#endregion


#region getbits
def getBits(amount: int, array: READABLE_ARRAY, startBit: int) -> int:
    bitfield = 0
    if amount <= 8:
        bitfield = byteFromBits(array, startBit)
    elif amount <= 16:
        bitfield = ushortFromBits(array, startBit)
    elif amount <= 32:
        bitfield = uintFromBits(array, startBit)
    elif amount <= 64:
        bitfield = ulongFromBits(array, startBit)
    bitfield &= ((1 << amount) - 1)
    return bitfield


def getBitsToBytes(array: READABLE_ARRAY, count: int, startBit: int) -> READABLE_ARRAY:
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE

    if bit == 0:
        return array[pos:pos+count]
    else:
        val = []
        for i in range(count):
            val.append(((array[i] >> bit) | (array[i+1] << (8 - bit)))&0xff)
        return bytes(val)
#endregion


#region byte
def byteToBits(value: int, array: WRITEABLE_ARRAY, startBit: int):
    pos = startBit // BITS_PER_BYTE
    bit = startBit % BITS_PER_BYTE

    if bit == 0:
        array[pos] = value & 0xff
    else:
        array[pos] |= (value << bit) & 0xff
        array[pos+1] = (value >> (8 - bit)) & 0xff
    return array


def byteFromBits(array: READABLE_ARRAY, startBit: int, byteorder: Literal['big', 'little'] = 'little'):
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE

    val = array[pos]
    if bit == 0:
        return val

    val >>= bit
    return val | array[pos+1] << (8 - bit)

#endregion


#region short
def ushortToBits(value: int, array: WRITEABLE_ARRAY, startBit: int):
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE
    if bit == 0:
        array[pos] = value & 0xff
        array[pos + 1] = (value >> 8) & 0xff
    else:
        array[pos] |= (value << bit) & 0xff
        value >>= 8 - bit
        array[pos + 1] = value & 0xff
        array[pos + 2] = (value >> 8) & 0xff
    return array


def ushortFromBits(array: READABLE_ARRAY, startBit: int, byteorder: Literal['big', 'little'] = 'little'):
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE

    val = array[pos] | array[pos+1] << 8
    if bit == 0:
        return val & 0xffff

    val >>= bit
    return (val | array[pos+2] << (16 - bit)) & 0xffff

#endregion


#region int

def uintToBits(value: int, array: WRITEABLE_ARRAY, startBit: int):
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE
    if bit == 0:
        array[pos] = value & 0xff
        array[pos + 1] = (value >> 8) & 0xff
        array[pos + 2] = (value >> 16) & 0xff
        array[pos + 3] = (value >> 24) & 0xff
    else:
        array[pos] = (value << bit) & 0xff
        value >>= 8 - bit
        array[pos + 1] = value & 0xff
        array[pos + 2] = (value >> 8) & 0xff
        array[pos + 3] = (value >> 16) & 0xff
        array[pos + 4] = (value >> 24) & 0xff
    return array


def uintFromBits(array: READABLE_ARRAY, startBit: int):
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE

    val = array[pos] | array[pos + 1] << 8 | array[pos + 2] << 16 | array[pos + 3] << 24
    if bit == 0:
        return val

    val >>= bit
    return val | array[pos + 4] << (32 - bit)


#endregion

#region long

def ulongToBits(value: int, array: WRITEABLE_ARRAY, startBit: int):
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE
    if bit == 0:
        array[pos] = value & 0xff
        array[pos + 1] = (value >> 8) & 0xff
        array[pos + 2] = (value >> 16) & 0xff
        array[pos + 3] = (value >> 24) & 0xff
        array[pos + 4] = (value >> 32) & 0xff
        array[pos + 5] = (value >> 40) & 0xff
        array[pos + 6] = (value >> 48) & 0xff
        array[pos + 7] = (value >> 56) & 0xff
    else:
        array[pos] = (value << bit) & 0xff
        value >>= 8 - bit
        array[pos + 1] = value & 0xff
        array[pos + 2] = (value >> 8) & 0xff
        array[pos + 3] = (value >> 16) & 0xff
        array[pos + 4] = (value >> 24) & 0xff
        array[pos + 5] = (value >> 32) & 0xff
        array[pos + 6] = (value >> 40) & 0xff
        array[pos + 7] = (value >> 48) & 0xff
        array[pos + 8] = (value >> 56) & 0xff
    return array


def ulongFromBits(array: READABLE_ARRAY, startBit: int):
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE

    val = array[pos] | array[pos + 1] << 8 | array[pos + 2] << 16 | array[pos + 3] << 24 | array[pos + 4] << 32 | array[pos + 5] << 40 | array[pos + 6] << 48 | array[pos + 7] << 56
    if bit == 0:
        return val

    val >>= bit
    return val | array[pos + 8] << (64 - bit)

#endregion


#region bytes
def bytesToBits(value: READABLE_ARRAY, array: WRITEABLE_ARRAY, startBit: int):
    pos: int = startBit // BITS_PER_BYTE
    bitoffset: int = startBit % BITS_PER_BYTE
    byte_count = len(value)

    if bitoffset == 0:
        for i in range(byte_count):
            array[pos + i] = (value[i]) & 0xff
    else:
        for i in range(byte_count):
            array[pos + i] = ((array[pos + i] & (0xff >> (8 - bitoffset))) | (value[i] << bitoffset)) & 0xff
            array[pos + i + 1] = ((array[pos + i + 1] & (0xff << bitoffset)) | (value[i] >> (8 - bitoffset))) & 0xff

    #if bit == 0:
    #    for i in range(bcount):
    #        array[pos + i] = (value[i]) & 0xff
    #else:
    #    for i in range(bcount):
    #        array[pos + i] = (((value[i] << bit) & (0xff << bit)) | (array[pos + i] & (0xff  >> (8 - bit)))) & 0xff
    #        array[pos + i + 1] = (((value[i] >> (8 - bit)) & (0xff >> (8 - bit))) | (array[pos + i + 1] & (0xff << bit))) & 0xff
    return array


def bytesFromBits(array: READABLE_ARRAY, count: int, startBit: int) -> READABLE_ARRAY:
    """
    :param array: array to read bytes from
    :param count: bit count IN BITS
    :param startBit: Start bit in BITS
    """
    pos: int = startBit // BITS_PER_BYTE
    bit: int = startBit % BITS_PER_BYTE
    byteCount = int(ceil(float(count) / BITS_PER_BYTE))

    if bit == 0:
        return array[pos:pos+byteCount]
    else:
        val = []
        for i in range(byteCount - 1):
            val.append((array[pos + i] >> bit) | (array[pos + i + 1] << (8 - bit)) & 0xff)
        if len(array) > pos + byteCount:
            val.append((array[pos + byteCount - 1] >> bit) | (array[pos + byteCount] << (8 - bit)) & 0xff)
        else:
            val.append((array[pos + byteCount - 1] >> bit) & 0xff)

        return bytes(val)
#endregion

#endregion

#region VarLen

def toVarLong(value: int) -> WRITEABLE_ARRAY:
    return toVarULong(zigzagEncode64(value))


def fromVarLong(data: READABLE_ARRAY, pos: int = 0):
    r, c = fromVarULong(data, pos)
    return zigzagDecode(r), c


def toVarULong(value: int) -> WRITEABLE_ARRAY:
    if value < 0:
        raise Exception("Value MUST be positive. Use ZigZag encoding for negative values")

    tmp_data = []

    while True:
        byte_val = value & 0b_0111_1111
        value >>= 7
        if value != 0:
            byte_val |= 0b1000_0000
            tmp_data.append(byte_val)
        else:
            tmp_data.append(byte_val)
            break
    return tmp_data


def fromVarULong(data: READABLE_ARRAY, pos: int = 0):
    shift = 0
    val = 0
    bytes_read = 0
    while True:

        byte_val = byteFromBits(data, pos + (bytes_read * BITS_PER_BYTE))
        val |= (byte_val & 0b0111_1111) << shift
        bytes_read += 1
        shift += 7

        if (byte_val & 0b1000_0000) == 0:
            break
    return val, bytes_read*BITS_PER_BYTE

#endregion

#region Floating point
#Todo: Switch format strings based on byteorder


def fp32_to_bytes(value: float, byteorder: Literal['big', 'little'] = 'little') -> bytearray:
    """
    Converts a 32 bit float to bytes

    :param value: Value to convert
    :param byteorder: byteorder to use, defaults to little endian
    :return: the resulting bytes
    """
    return bytearray(struct.pack(FLOAT_LITTLE, value))


def fp64_to_bytes(value: float, byteorder: Literal['big', 'little'] = 'little') -> bytearray:
    """
    Converts a 64 bit float to bytes

    :param value: Value to convert
    :param byteorder: byteorder to use, defaults to little endian
    :return: the resulting bytes
    """
    return bytearray(struct.pack(DOUBLE_LITTLE, value))


def bytes_to_fp32(value: bytes, byteorder: Literal['big', 'little'] = 'little') -> float:
    """
    Converts 4 bytes to a 32 bit float

    :param value: bytes to convert from
    :param byteorder: byteorder to use, defaults to little endian
    :return: the resulting float value
    """
    return struct.unpack(FLOAT_LITTLE, value)[0]


def bytes_to_fp64(value: bytes, byteorder: Literal['big', 'little'] = 'little') -> float:
    """
    Converts 8 bytes to a 64 bit float

    :param value: bytes to convert from
    :param byteorder: byteorder to use, defaults to little endian
    :return: the resulting float value
    """
    return struct.unpack(DOUBLE_LITTLE, value)[0]
#endregion