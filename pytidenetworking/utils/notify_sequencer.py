# Updated to 2.1.0

from typing import TYPE_CHECKING

from .converter import BITS_PER_BYTE
from .sequencer import Sequencer
from ..message_base import MessageBase, HEADER_BITS
from .helper import getSequenceGap

if TYPE_CHECKING:
    from ..connection import Connection


class NotifySequencer(Sequencer):

    def __init__(self, connection: 'Connection'):
        super(NotifySequencer, self).__init__(connection)

    def insertHeader(self, message: MessageBase) -> int:
        sequenceID = self.nextSequenceID
        notify_bits = self._lastReceivedSeqId | (self.receivedSeqIds.first8 << (2 * BITS_PER_BYTE)) | (sequenceID << (3 * BITS_PER_BYTE))
        message.setNotifyBits(notify_bits)
        return sequenceID

    def shouldHandle(self, sequenceID: int) -> bool:
        sequenceGap = getSequenceGap(sequenceID, self.lastReceivedSeqId)

        if sequenceGap > 0:
            self.receivedSeqIds <<= sequenceGap
            self._lastReceivedSeqId = sequenceID

            if self.receivedSeqIds.isSet(sequenceGap):
                return False

            self.receivedSeqIds.set(sequenceGap)
            return True
        return False

    def updateReceivedAcks(self, remoteLastReceivedSeqId: int, remoteReceivedSeqIds: int):
        sequenceGap = getSequenceGap(remoteLastReceivedSeqId, self._lastReceivedSeqId)

        if sequenceGap > 0:
            if sequenceGap > 1:
                # handle messages in the gap
                while sequenceGap > 9:
                    self.lastAckedSeqId += 1
                    sequenceGap -= 1
                    self.connection.notifyLost(self.lastAckedSeqId)

                bitCount = sequenceGap -1
                bit = 1 << bitCount

                for i in range(bitCount):
                    self.lastAckedSeqId += 1
                    bit >>= 1
                    if remoteReceivedSeqIds & bit == 0:
                        self.connection.onNotifyLost(self.lastAckedSeqId)
                    else:
                        self.connection.onNotifyDelivered(self.lastAckedSeqId)

            self._lastAckedSeqId = remoteLastReceivedSeqId
            self.connection.onNotifyDelivered(self._lastAckedSeqId)
