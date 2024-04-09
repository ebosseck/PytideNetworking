# Updated to 2.1.0

from pytidenetworking.utils.rolling_stat import RollingStat


class ConnectionMetrics:

    def __init__(self):
        self.__unreliableBytesIn: int = 0
        self.__unreliableBytesOut: int = 0
        self.__unreliableIn: int = 0
        self.__unreliableOut: int = 0

        self.__notifyBytesIn: int = 0
        self.__notifyBytesOut: int = 0
        self.__notifyIn: int = 0
        self.__notifyOut: int = 0
        self.__notifyDiscarded: int = 0
        self.__notifyLost: int = 0
        self.__notifyDelivered: int = 0
        self.__rollingNotifyLost: int = 0
        self.__rollingNotifyDelivered: int = 0

        self.__reliableBytesIn: int = 0
        self.__reliableBytesOut: int = 0
        self.__reliableIn: int = 0
        self.__reliableOut: int = 0
        self.__reliableDiscarded: int = 0
        self.__reliableUniques: int = 0

        self.rollingReliableSends: RollingStat = RollingStat(64)

        self.__notifyLossTracker: int = 0
        self.__notifyBufferCount: int = 0

    def reset(self):
        self.__unreliableBytesIn: int = 0
        self.__unreliableBytesOut: int = 0
        self.__unreliableIn: int = 0
        self.__unreliableOut: int = 0

        self.__notifyBytesIn: int = 0
        self.__notifyBytesOut: int = 0
        self.__notifyIn: int = 0
        self.__notifyOut: int = 0
        self.__notifyDiscarded: int = 0
        self.__notifyLost: int = 0
        self.__notifyDelivered: int = 0

        self.__reliableBytesIn: int = 0
        self.__reliableBytesOut: int = 0
        self.__reliableIn: int = 0
        self.__reliableOut: int = 0
        self.__reliableDiscarded: int = 0
        self.__reliableUniques: int = 0

    @property
    def bytesIn(self) -> int:
        return self.__unreliableBytesIn + self.__reliableBytesIn + self.__notifyBytesIn

    @property
    def bytesOut(self) -> int:
        return self.__unreliableBytesOut + self.__reliableBytesOut + self.__notifyBytesOut

    @property
    def messagesIn(self) -> int:
        return self.__unreliableIn + self.__reliableIn + self.__notifyIn

    @property
    def messagesOut(self) -> int:
        return self.__unreliableOut + self.__reliableOut + self.__notifyOut

    @property
    def unreliableBytesIn(self) -> int:
        return self.__unreliableBytesIn

    @property
    def unreliableBytesOut(self) -> int:
        return self.__unreliableBytesOut

    @property
    def unreliableIn(self) -> int:
        return self.__unreliableIn

    @property
    def unreliableOut(self) -> int:
        return self.__unreliableOut

    @property
    def notifyBytesIn(self) -> int:
        return self.__notifyBytesIn

    @property
    def notifyBytesOut(self) -> int:
        return self.__notifyBytesOut

    @property
    def notifyIn(self) -> int:
        return self.__notifyIn

    @property
    def notifyOut(self) -> int:
        return self.__notifyOut

    @property
    def notifyDiscarded(self) -> int:
        return self.__notifyDiscarded

    @property
    def notifyLost(self) -> int:
        return self.__notifyLost

    @property
    def notifyDelivered(self) -> int:
        return self.__notifyDelivered

    @property
    def rollingNotifyLost(self) -> int:
        return self.__rollingNotifyLost

    @property
    def rollingNotifyDelivered(self) -> int:
        return self.__rollingNotifyDelivered

    @property
    def rollingNotifyLossRate(self) -> float:
        return self.__rollingNotifyLost / 64.0

    @property
    def reliableBytesIn(self) -> int:
        return self.__reliableBytesIn

    @property
    def reliableBytesOut(self) -> int:
        return self.__reliableBytesOut

    @property
    def reliableIn(self) -> int:
        return self.__reliableIn

    @property
    def reliableOut(self) -> int:
        return self.__reliableOut

    @property
    def reliableDiscarded(self) -> int:
        return self.__reliableDiscarded

    @property
    def reliableUniques(self) -> int:
        return self.__reliableUniques

    def receivedUnreliable(self, byteCount: int):
        self.__unreliableBytesIn += byteCount
        self.__unreliableIn += 1

    def sentUnreliable(self, byteCount: int):
        self.__unreliableBytesOut += byteCount
        self.__unreliableOut += 1

    def receivedNotify(self, byteCount: int):
        self.__notifyBytesIn += byteCount
        self.__notifyIn += 1

    def sentNotify(self, byteCount: int):
        self.__notifyBytesOut += byteCount
        self.__notifyOut += 1

    def deliveredNotify(self):
        self.__notifyDelivered += 1
        if self.__notifyBufferCount < 64:
            self.__rollingNotifyDelivered += 1
            self.__notifyBufferCount += 1
        elif self.__notifyLossTracker & (1 << 63) == 0:
            self.__rollingNotifyDelivered += 1
            self.__notifyLost -= 1
        self.__notifyLossTracker <<= 1
        self.__notifyLossTracker |= 1

    def lostNotify(self):
        self.__notifyLost += 1
        if self.__notifyBufferCount < 64:
            self.__rollingNotifyLost += 1
            self.__notifyBufferCount += 1
        elif self.__notifyLossTracker & (1 << 63) != 0:
            self.__rollingNotifyDelivered -= 1
            self.__rollingNotifyLost += 1
        self.__notifyLossTracker <<= 1

    def receivedReliable(self, byteCount: int):
        self.__reliableBytesIn += byteCount
        self.__reliableIn += 1

    def sentReliable(self, byteCount: int):
        self.__reliableBytesOut += byteCount
        self.__reliableOut += 1

    def incrementReliableUniques(self):
        self.__reliableUniques += 1

    def incrementNotifyDiscarded(self):
        self.__notifyDiscarded += 1

    def incrementReliableDiscarded(self):
        self.__reliableDiscarded += 1
