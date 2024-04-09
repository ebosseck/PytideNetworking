# Updated to 2.1.0

from typing import Union, List, Tuple

from pytidenetworking.connection import Connection
from pytidenetworking.transports.udp.udp_peer import UDPPeer


class UDPConnection(Connection):

    def __init__(self, remoteEndpoint: Tuple[str, int], peer: UDPPeer):
        super(UDPConnection, self).__init__()
        self.remoteEndpoint = remoteEndpoint

        self.__udpPeer = peer

    def __hash__(self):
        return self.remoteEndpoint.__hash__()

    def __str__(self):
        return "{}:{}".format(*self.remoteEndpoint)

    def __eq__(self, other):
        if not isinstance(other, UDPConnection):
            return False
        if self is None:
            if other is None:
                return True
            return False
        if other is None:
            return False
        return self.remoteEndpoint == other.remoteEndpoint

    def __ne__(self, other):
        return not self.__eq__(other)

    def send(self, dataBuffer: Union[bytes, bytearray, List[int]], amount: int):
        """
        Sends data

        :param dataBuffer: data to send
        :param amount: number of bytes to send
        """
        self.__udpPeer.send(dataBuffer, amount, self.remoteEndpoint)
