import struct
from typing import Literal


FLOAT_LITTLE = "<f"
DOUBLE_LITTLE = "<d"

FLOAT_BIG = ">f"
DOUBLE_BIG = ">d"

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