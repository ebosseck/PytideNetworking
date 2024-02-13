# Updated to 2.1.0
from typing import Tuple


class Bitfield:

    def __init__(self, isDynamicCapacity: bool = True):
        self.__isDynamicCapacity = isDynamicCapacity
        self.__bits = 0
        self.__count = 0
        self.__capacity = 4 * 4 * 8 # 4 segemnts, 4 byte / segment, 8 bit / byte

    @property
    def first8(self):
        return self.__bits & 0xff

    @property
    def first16(self):
        return self.__bits & 0xffff

    def hasCapacityFor(self, amount: int):
        overflow = self.__count + amount - self.__capacity
        return overflow < 0, overflow

    def __lshift__(self, value: int):
        if not isinstance(value, int):
            raise Exception("Invalid Type, expected int")
        if not self.__isDynamicCapacity:
            self.__count = min(self.__count + value, 4*8)
        else:
            if not self.hasCapacityFor(value):
                self.trim()
            self.__count += value
            self.__capacity = self.__count

        self.__bits <<= value
        if not self.__isDynamicCapacity:
            self.__bits = self.__bits & (2**self.__capacity)
        return self

    def isSet(self, bit: int) -> bool:
        if (bit > self.__count):
            return True
        if (bit < 1):
            raise Exception('bit must be greater than zero!')
        bit -= 1

        return self.__bits & (1 << bit) != 0

    def set(self, bit):
        if (bit < 1):
            raise Exception('bit must be greater than zero!')
        bit -= 1
        self.__bits |= (1 << bit)

    def checkAndTrimLast(self) -> Tuple[bool, int]:
        checkedPos = self.__count
        bitToCheck = (1 << (self.__count - 1))
        isSet = self.__bits & bitToCheck != 0
        self.__count -= 1
        return isSet, checkedPos

    def trim(self):
        while self.__count > 0 and self.isSet(self.__count):
            self.__count -= 1

    def combine(self, other: int):
        self.__bits |= other
