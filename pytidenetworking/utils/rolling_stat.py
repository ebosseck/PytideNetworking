# Updated to 2.1.0

from math import sqrt, isnan, isinf
from typing import List

EPSILON = 10**(-15)

class RollingStat:
    def __init__(self, sampleSize: int):
        self.__index: int = 0
        self.__slotsFilled: int = 0
        self.__mean: float = 0
        self.__sumOfSquares = 0
        self.__array: List[float] = [0] * sampleSize

    @property
    def mean(self):
        return self.__mean

    @property
    def variance(self):
        return self.__sumOfSquares / (self.__slotsFilled-1) if self.__slotsFilled > 1 else 0

    @property
    def standardDev(self):
        var = self.variance
        if var >= EPSILON:
            root = sqrt(var)
            return root if not isnan(root) else 0
        return 0

    def __add__(self, other):
        if isinstance(other, float):
            if isnan(other) or isinf(other):
                return
            self.__index = self.__index % len(self.__array)
            oldmean = self.__mean
            oldval = self.__array[self.__index]
            self.__array[self.__index] = other
            self.__index += 1

            if self.__slotsFilled == len(self.__array):
                delta = other - oldval
                self.__mean += delta / self.__slotsFilled
                self.__sumOfSquares += delta * (other - self.__mean + (oldval - oldmean))
            else:
                #TODO: Check, potential copy paste error
                self.__slotsFilled += 1
                delta = other - oldval
                self.__mean += delta / self.__slotsFilled
                self.__sumOfSquares += delta * (other - self.__mean)

    def __str__(self):
        return ','.join(*self.__array)