DC_NEVER_CONNECTED = "Never connected"
DC_TRANSPORT_ERROR = "Transport error"
DC_TIMED_OUT = "Timed out"
DC_KICKED = "Kicked"
DC_SERVER_STOPPED = "Server stopped"
DC_DISCONNECTED = "Disconnected"
DC_POOR_CONNECTION = "Poor Connection"
UNKNOWN_REASON = "Unknown reason"
CR_NO_CONNECTION = "No connection"
CR_SERVER_FULL = "Server is full"
CR_REJECTED = "Rejected"
CR_CUSTOM = "Rejected with custom reason"


_ACTIVE_COUNT = 0


def increaseActiveCount():
    """
    Increments the amount of active connections
    :return:
    """
    global _ACTIVE_COUNT
    _ACTIVE_COUNT += 1


def decreaseActiveCount():
    """
    Decrements the amount of active connections
    :return:
    """
    global _ACTIVE_COUNT
    _ACTIVE_COUNT = max(0, _ACTIVE_COUNT-1)


@property
def activeCount():
    """
    :return: the number of currently active connections
    """
    return _ACTIVE_COUNT
