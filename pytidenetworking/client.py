# Updated to 2.1.0
from typing import Optional, Dict, Callable, Union, Tuple, List

from .connection import Connection
from .message import Message, createInternal as createMessage
from .message_base import MessageHeader
from .peer import Peer, DisconnectReason, RejectReason, increaseActiveCount, decreaseActiveCount, HeartbeatEvent, \
    rejectReasonToString, disconnectReasonToString
from .transports.iclient import IClient
from .transports.udp.udp_client import UDPClient
from .utils.eventhandler import EventHandler
from .utils.logengine import getLogger

logger = getLogger("pytide.client")

class Client(Peer):
    """A Client that connects to a Server"""
    def __init__(self, transport: IClient = None):
        """
        Initialisation
        :param transport: The transport to use for sending and receiving data.
        """
        super(Client, self).__init__()

        self.Connected: EventHandler = EventHandler()
        """
        Invoked when a connection to the server is established.
        """

        self.ConnectionFailed: EventHandler = EventHandler()
        """
        Invoked when a connection to the server fails to be established.
        """

        self.MessageReceived: EventHandler = EventHandler()
        """
        Invoked when a message is received.
        """

        self.Disconnected: EventHandler = EventHandler()
        """
        Invoked when disconnected from the server.
        """

        self.ClientConnected: EventHandler = EventHandler()
        """
        Invoked when another non-local client connects.
        """

        self.ClientDisconnected: EventHandler = EventHandler()
        """
        Invoked when another non-local client disconnects.
        """

        self.__connection: Optional[Connection] = None
        """
        The client's connection to a server.
        """

        self.__connectionAttempts: int = 0
        """
        How many connection attempts have been made so far.
        """

        self.__maxConnectionAttempts: int = 0
        """
        How many connection attempts to make before giving up.
        """

        self.__messageHandlers: Dict[int, Callable[[Message], None]] = {}
        """
        Methods used to handle messages, accessible by their corresponding message IDs
        """

        self.__transport: IClient = transport
        """
        The underlying transport's client that is used for sending and receiving data.
        """

        if self.__transport is None:
            self.__transport = UDPClient()

        #self.__connectBytes: Optional[bytearray] = None
        #"""
        #Custom data to include when connecting.
        #"""

        self.__connectMessage: Optional[Message] = None
        """
        The message sent when connecting, may include custom data
        """

    #region Properties

    @property
    def id(self):
        """
        :return: The client's numeric ID.
        """
        return self.__connection.id

    @property
    def rtt(self):
        """
        The round trip time (ping) of the connection, in milliseconds. -1 if not calculated yet.
        """
        return self.__connection.rtt

    @rtt.setter
    def rtt(self, value):
        """
        The round trip time (ping) of the connection, in milliseconds. -1 if not calculated yet.
        """
        self.__connection.rtt = value

    @property
    def smoothRTT(self):
        """
        The smoothed round trip time (ping) of the connection, in milliseconds. -1 if not calculated yet.

        This value is slower to accurately represent lasting changes in latency than rtt, but it is less susceptible to
        changing drastically due to significant—but temporary—jumps in latency.

        :return:
        """
        return self.__connection.smoothRTT

    @property
    def timeoutTime(self):
        """
        """
        pass

    @timeoutTime.setter
    def timeoutTime(self, value):
        self.defaultTimeout = value

    # region Connection State
    @property
    def isNotConnected(self) -> bool:
        """
        :return: True if the client is currently not connected nor trying to connect.
        """
        if self.__connection is None:
            return True
        return self.__connection.isNotConnected

    @property
    def isConnecting(self) -> bool:
        """
        :return: True if the client is currently in the process of connecting
        """
        if self.__connection is None:
            return False
        return self.__connection.isConnecting

    @property
    def isPending(self) -> bool:
        """
        :return: True if the client's connection is currently pending (will only be True when a server doesn't
        immediately accept the connection request)
        """
        if self.__connection is None:
            return False
        return self.__connection.isPending

    @property
    def isConnected(self) -> bool:
        """
        :return: True if the client is currently connected.
        """
        if self.__connection is None:
            return False
        return self.__connection.isConnected
    # endregion

    #endregion

    #region Message Handlers

    def registerMessageHandler(self, messageID: int, callback: Callable[[Message], None]):
        """
        Registers a handler for messages with the given ID

        :param messageID: Message ID handled by the handler
        :param callback: MessageHandler for messages with the given ID
        :return:
        """
        self.__messageHandlers[messageID] = callback

    def removeMessageHandler(self, messageID: int):
        """
        Removes the handler for messages with the given ID

        :param messageID: Message ID of handler to remove
        :return:
        """
        del self.__messageHandlers[messageID]

    #endregion

    def changeTransport(self, transport: IClient):
        """
        Disconnects the client if it's connected and swaps out the transport it's using.

        This method does not automatically reconnect to the server. To continue communicating with the server,
        Connect() must be called again.

        :param transport: The new transport to use for sending and receiving data.
        :return:
        """
        self.disconnect()
        self.__transport = transport

    def connect(self, hostAddress: Tuple[str, int], maxConnectionAttempts: int = 5, messageHandlerGroupId: int = 0,
                message: Message = None, useMessageHandlers:bool = True):
        """
        Attempts to connect to a server at the given host address

        :param hostAddress: Address of the server to connect to
        :param maxConnectionAttempts: How many connection attempts to make before giving up
        :param messageHandlerGroupId: Currently unused
        :param message: Data that should be sent to the server with the connection attempt.
        :param useMessageHandlers: if true, use message handlers (default behaviour)
        Use message.createInternal() to get an empty message instance
        :return:
        """
        self.disconnect()
        self.subToTransportEvents()

        success, connection, connectError = self.__transport.connect(*hostAddress)

        if not success:
            logger.error(connectError)
            self.unsubToTransportEvents()
            return success

        self.__connection: Connection = connection

        self.__maxConnectionAttempts = maxConnectionAttempts
        self.__connectionAttempts = 0
        #self.__connection._peer = self
        self.__connection.initialize(self, self._defaultTimeout)
        increaseActiveCount()

        if useMessageHandlers:
            pass
            #TODO: Register message handlers automatically from attributes ?

        self.__connectMessage: Message = createMessage(MessageHeader.Connect)
        if message is not None:
            if message.readBit != 0:
                logger.error("Use the parameterless 'Message.Create()' overload when setting connection attempt data!")
            self.__connectMessage.appendMessage(message)
            message.release()

        self.startTime()
        self.heartbeat()
        logger.info("Connecting to {}:{}".format(*hostAddress))

        return True

    def subToTransportEvents(self):
        """
        Subscribes appropriate methods to the transport's events.

        :return:
        """
        self.__transport.Connected += self.onTransportConnected
        self.__transport.ConnectionFailed += self.onTransportConnectionFailed
        self.__transport.DataReceived += self._handleData
        self.__transport.Disconnected += self.onTransportDisconnected

    def unsubToTransportEvents(self):
        """
        Unsubscribes methods from all of the transport's events.

        :return:
        """
        self.__transport.Connected -= self.onTransportConnected
        self.__transport.ConnectionFailed -= self.onTransportConnectionFailed
        self.__transport.DataReceived -= self._handleData
        self.__transport.Disconnected -= self.onTransportDisconnected

    def heartbeat(self):
        """Checks the connection health"""
        if self.isConnecting:
            if self.__connectionAttempts < self.__maxConnectionAttempts:
                #message: Message = createMessage(MessageHeader.Connect)
                #if self.__connectBytes is not None:
                #   message.putBytes(self.__connectBytes)
                self.send(self.__connectMessage, False)
                self.__connectionAttempts += 1
            else:
                self.localDisconnect(DisconnectReason.NeverConnected)
                # TODO: Check in future if here is a return missing
        elif self.isPending:
            if self.__connection.hasConnectAttemptTimedOut:
                self.localDisconnect(DisconnectReason.NeverConnected)
                return
        elif self.isConnected:
            if self.__connection.hasTimedOut:
                self.localDisconnect(DisconnectReason.TimedOut)
                return
            self.__connection.sendHeartbeat()

        self.executeLater(self.heartbeat_interval, HeartbeatEvent(priority=self.heartbeat_interval + self.current_time,
                                                                  peer=self))

    def update(self):
        """
        Handles any received messages and invokes any delayed events which need to be invoked.

        :return:
        """
        super(Client, self).update()
        self.__transport.poll()
        self._handleMessages()

    def handle(self, message: Message, header: Union[MessageHeader, int], connection: Connection):
        """
        Handles a message

        :param message: Message to handle
        :param header: Header of the message to handle
        :param connection: connection the message came from
        :return:
        """
        if header == MessageHeader.Unreliable or header == MessageHeader.Reliable:
            self.onMessageReceived(message)
        # Internal Messages
        elif header == MessageHeader.Ack:
            self.__connection.handleAck(message)
        #elif header == MessageHeader.AckExtra:
        #    self.__connection.handleAckExtra(message)
        elif header == MessageHeader.Connect:
            self.__connection.setPending()
        elif header == MessageHeader.Reject:
            #reason = message.getUInt8()
            #if reason == RejectReason.Pending:
            #    self.__connection.setPending()
            #elif not self.isConnected:
            #    self.localDisconnect(reason=DisconnectReason.ConnectionRejected, message=message, rejectReason=reason)
            if not self.isConnected:
                self.localDisconnect(reason=DisconnectReason.ConnectionRejected, message=message, rejectReason=message.getByte())
        elif header == MessageHeader.Heartbeat:
            self.__connection.handleHeartbeatResponse(message=message)
        elif header == MessageHeader.Disconnect:
            self.localDisconnect(message.getUInt8(), message)
        elif header == MessageHeader.Welcome:
            if self.isConnecting or self.isPending:
                self.__connection.handleWelcome(message)
                self.onConnected()
        elif header == MessageHeader.ClientConnected:
            self.onClientConnected(message.getUInt16())
        elif header == MessageHeader.ClientDisconnected:
            self.onClientDisconnected(message.getUInt16())
        else:
            logger.warning("Unexpected message header '{}'. Discarding {} bytes.".format(header, message.bytesInUse))

        message.release()

    def send(self, message: Message, shouldRelease: bool = True) -> int:
        """
        Sends the given message
        :param message: Message to send
        :param shouldRelease: True if the message should be released back into the pool. Defaults to true.
        :return:
        """
        return self.__connection.sendMessage(message, shouldRelease)

    def disconnect(self, connection: Connection = None, reason: DisconnectReason = None):
        """
        Disconnect this client from the server
        :return:
        """
        if connection is None and reason is None:
            if self.__connection is None or self.isNotConnected:
                return

            self.send(createMessage(MessageHeader.Disconnect))
            self.localDisconnect(DisconnectReason.Disconected)
        else:
            if connection.isConnected and connection.canQualityDisconnect:
                self.localDisconnect(reason)

    def localDisconnect(self, reason: Union[DisconnectReason, int], message: Message = None,
                        rejectReason: Union[RejectReason, int] = RejectReason.NoConnection):
        """
        Cleans up the local side of the connection.

        :param reason: The reason why the client has disconnected.
        :param message: The disconnection or rejection message, potentially containing extra data to be handled externally.
        :param rejectReason: Reason the client was recected, only present if the disconnect reason is ConnectionRejected
        :return:
        """
        if self.isNotConnected:
            return

        self.unsubToTransportEvents()
        decreaseActiveCount()

        self.stopTime()

        self.__transport.disconnect()
        self.__connection.localDisconnect()

        if reason == DisconnectReason.NeverConnected:
            self.onConnectionFailed(RejectReason.NoConnection)
        elif reason == DisconnectReason.ConnectionRejected:
            self.onConnectionFailed(rejectReason, message)
        else:
            self.onDisconnected(reason, message)

    #region Transport Event Handlers

    def onTransportConnected(self):
        """
        What to do when the transport establishes a connection.
        :return:
        """
        pass
        #self.startTime()

    def onTransportConnectionFailed(self):
        """
        What to do when the transport fails to connect.
        :return:
        """
        self.localDisconnect(DisconnectReason.NeverConnected)

    def onTransportDisconnected(self, connection: Connection, reason: Union[DisconnectReason, int]):
        """
        What to do when the transport disconnects.

        :param connection: Connection that disconnected
        :param reason: Reason why the connection disconnected
        :return:
        """
        if self.__connection == connection:
            self.localDisconnect(reason)

    #endregion

    #region Event Handlers
    def onConnected(self):
        """
        Invokes the connected event

        :return:
        """
        logger.info("Connected Successfully !")
        self.__connectMessage.release()
        self.__connectMessage = None
        self.Connected()

    def onConnectionFailed(self, rejectReason: Union[RejectReason, int], message: Message = None):
        """
        Invokes the Connection Failed event

        :param rejectReason: reason for the connection failure
        :param message: Additional data to the failed connection attempt
        :return:
        """
        self.__connectMessage.release()
        self.__connectMessage = None
        logger.info("Connection to server failed: {}".format(rejectReasonToString(rejectReason)))
        self.ConnectionFailed(message)


    def onMessageReceived(self, message: Message):
        """
        Invokes the MessageReceived event and initiates handling of the received message.

        :param message: the received message
        :return:
        """
        messageID = message.msgID
        self.MessageReceived(self.__connection, messageID, message)
        if self._useMessageHandlers:
            if messageID in self.__messageHandlers:
                self.__messageHandlers[messageID](message)
            else:
                logger.warning("No message handler method found for message ID '{}'".format(messageID))

    def onDisconnected(self, reason: Union[DisconnectReason, int], message: Message):
        """
        Invokes the disconnected event

        :param reason: Reason for the disconnection
        :param message: Additional data related to the disconnection
        :return:
        """
        logger.info("Disconnected from Server: {}".format(disconnectReasonToString(reason)))
        self.Disconnected(reason, message)

    def onClientConnected(self, clientID: int):
        """
        Invokes the client connected event
        :param clientID: Numeric ID of the client that connected
        :return:
        """
        logger.info("Client '{}' connected".format(clientID))
        self.ClientConnected(clientID)

    def onClientDisconnected(self, clientID: int):
        """
        Invokes the Client Disconnected event

        :param clientID: The numeric ID of the client that disconnected
        :return:
        """
        logger.info("Client '{}' disconnected".format(clientID))
        self.ClientDisconnected(clientID)

    #endregion
