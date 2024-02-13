# Updated to 2.1.0

from typing import TYPE_CHECKING

from .bitfield import Bitfield

if TYPE_CHECKING:
    from ..connection import Connection


class Sequencer:

    def __init__(self, connection: 'Connection'):
        self.__nextSequenceId = 1
        self.connection = connection

        self.lastReceivedSeqId = 0
        self.receivedSeqIds = Bitfield()
        self.lastAckedSeqId = 0
        self.ackedSeqIds = Bitfield()

    @property
    def nextSequenceID(self):
        """

        :return: The next sequence ID to use.
        """
        self.__nextSequenceId += 1 & 0xffff # Ushort with overflow behaviour
        return self.__nextSequenceId

    def shouldHandle(self, sequenceID: int) -> bool:
        pass

    def updateReceivedAcks(self, remoteLastReceivedSeqId: int, remoteReceivedSeqIds: int):
        pass
