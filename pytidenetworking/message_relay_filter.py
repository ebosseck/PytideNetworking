from typing import List

class MessageRelayFilter:
    """
    Filter whether the message with the given ID should be relayed to all clients or not
    """
    def __init__(self, idsToEnable: List[int] = None):
        """
        Constructor

        :param idsToEnable: List of MessageIDs to enable for relaying, defaults to None
        """
        self.__filter: int = 0

        if idsToEnable is not None:
            self.enableIDs(idsToEnable)

    def enableIDs(self, idsToEnable: List[int]):
        """
        Enable all given message IDs for relaying

        :param idsToEnable: List of message IDs to relay
        :return:
        """
        for id in idsToEnable:
            self.enableRelay(id)

    def clearFilter(self):
        """
        Disable relaying for all message IDs
        :return:
        """
        self.__filter = 0

    def enableRelay(self, forMessageId: int):
        """
        Enables Relaying for all messages with the given ID

        :param forMessageId: Message ID to start relaying
        :return:
        """
        self.__filter |= (1 << forMessageId)

    def disableRelay(self, forMessageId: int):
        """
        Disable relaying the given message ID

        :param forMessageId: Message ID to disable relaying for
        :return:
        """
        self.__filter &= ~(1 << forMessageId)

    def shouldRelay(self, forMessageId: int):
        """
        :param forMessageId: Message ID to check
        :return: True if messages with the given ID should be relayed, false otherwise
        """
        return self.__filter & (1 << forMessageId) != 0

    def __iadd__(self, other: int):
        """
        Add the given message ID to the message IDs to relay
        :param other:
        :return:
        """
        self.enableRelay(other)
        return self

    def __isub__(self, other: int):
        """Removes the given Message ID from the list of messages to relay"""
        self.disableRelay(other)
        return self