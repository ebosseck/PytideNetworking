# Updated to 2.1.0

from pytidenetworking.utils.eventhandler import EventHandler

class IPeer:
    """Defines methods, properties, and events which every transport's server and client must implement."""
    def __init__(self):
        self.DataReceived : EventHandler = EventHandler()
        """
        Invoked when data is received by the transport.
        """
        self.Disconnected : EventHandler = EventHandler()
        """
        Invoked when a disconnection is initiated or detected by the transport
        """

    def poll(self):
        """Initiates handling of any received messages"""
        pass