# Updated to 2.1.0

from typing import TYPE_CHECKING

from .helper import getSequenceGap
from .logengine import getLogger
from .sequencer import Sequencer

if TYPE_CHECKING:
    from ..connection import Connection

logger = getLogger("pytide.reliable_sequencer")

class ReliableSequencer(Sequencer):

    def __init__(self, connection: 'Connection'):
        super(ReliableSequencer, self).__init__(connection)

    def shouldHandle(self, sequenceID: int):
        doHandle = False
        sequenceGap = getSequenceGap(sequenceID, self.lastReceivedSeqId)

        if sequenceGap != 0:
            if sequenceGap > 0:
                if sequenceGap > 64:
                    logger.warning("The gap between received sequence IDs was very large ({})!".format(sequenceGap))
                self.receivedSeqIds <<= sequenceGap
                self.lastReceivedSeqId = sequenceID
            else:
                sequenceGap = -sequenceGap # ID is older than the previous one
            doHandle = not self.receivedSeqIds.isSet(sequenceGap)
            self.receivedSeqIds.set(sequenceGap)

        self.connection.sendAck(sequenceID, self.lastReceivedSeqId, self.receivedSeqIds)
        return doHandle

    def updateReceivedAcks(self, remoteLastReceivedSeqId: int, remoteReceivedSeqIds: int):
        sequenceGap = getSequenceGap(remoteLastReceivedSeqId, self.lastReceivedSeqId)

        if sequenceGap > 0:
            cap, overflow = self.ackedSeqIds.hasCapacityFor(sequenceGap)
            if not cap:
                for i in range(overflow):
                    check, checkedPosition = self.ackedSeqIds.checkAndTrimLast()
                    if not check:
                        self.connection.resendMessage(self.lastReceivedSeqId - checkedPosition)
                    else:
                        self.connection.clearMessage(self.lastReceivedSeqId - checkedPosition)

            self.ackedSeqIds <<= sequenceGap
            self.lastAckedSeqId = remoteLastReceivedSeqId

            for i in range(16):
                if not self.ackedSeqIds.isSet(i+1) and remoteReceivedSeqIds & (1 << i) != 0:
                    self.connection.clearMessage(self.lastAckedSeqId - (i + 1))

            self.ackedSeqIds.combine(remoteReceivedSeqIds)
            self.ackedSeqIds.set(sequenceGap)
            self.connection.clearMessage(remoteLastReceivedSeqId)
        elif sequenceGap < 0:
            self.ackedSeqIds.set(-sequenceGap)
        else:
            self.ackedSeqIds.combine(remoteReceivedSeqIds)
