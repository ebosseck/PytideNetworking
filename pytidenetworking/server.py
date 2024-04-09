# Updated to 2.1.0

from typing import List, Dict, Callable, Union, Tuple, Optional

from pytidenetworking.connection import Connection
from pytidenetworking.constants import decreaseActiveCount, increaseActiveCount
from pytidenetworking.message import Message, createInternal as createMessage
from pytidenetworking.message_base import MessageHeader
from pytidenetworking.peer import Peer, DisconnectReason, RejectReason, rejectReasonToString, HeartbeatEvent, \
    disconnectReasonToString
from pytidenetworking.transports.iserver import IServer
from pytidenetworking.transports.udp.udp_server import UDPServer
from pytidenetworking.utils.eventhandler import EventHandler
from pytidenetworking.utils.logengine import getLogger

logger = getLogger("pytide.Server")


class Server(Peer):
    """
    A server that can accept connections from Clients.
    """
    def __init__(self, transport: IServer = None):
        """
        Constructor
        :param transport: the Transport to use (Defaults to TCP)
        """
        super(Server, self).__init__()

        self.ClientConnected: EventHandler = EventHandler()
        """
        Invoked when a client connects.
        """
        self.ConnectionFailed: EventHandler = EventHandler()
        """
        Invoked when a connection fails to be fully established.
        """

        self.MessageReceived: EventHandler = EventHandler()
        """
        Invoked when a message is received
        """

        self.ClientDisconnected: EventHandler = EventHandler()
        """
        Invoked when a client disconnects
        """

        self.__isRunning = False
        """
        Whether or not the server is currently running
        """

        self.__maxClientCount = 5
        """
        The maximum number of concurrent connections
        """

        self.__transport: IServer = transport
        """
        The underlying transport's server that is used for sending and receiving data.
        """

        if self.__transport is None:
            self.__transport = UDPServer()

        self.messageRelayFilter = None
        """
        Stores which message IDs have auto relaying enabled. Relaying is disabled entirely when this is None
        """

        self.__pendingConnections: List[Connection] = []
        """
        Currently pending connections which are waiting to be accepted or rejected
        """

        self.__clients: Dict[int, Connection] = {}
        """
        Currently connected clients
        """

        self.__timedOutClients: List[Connection] = []
        """
        Clients that have timed out and need to be removed from the client dictionary
        """

        self.__messageHandlers: Dict[int, Callable[[int, Message], None]] = {}
        """
        Methods used to handle messages, accessible by their corresponding message IDs
        """

        self.__availableClientIDs: List[int] = []
        """
        All currently unused client IDs
        """

        self.handleConnection: Optional[Callable[[Connection, Message], None]] = None
        """
        a method that determines whether or not to accept a client's connection attempt
        """

    def handleConnection(self, connection: Connection, connectMessage: Message):
        """
        a method that determines whether or not to accept a client's connection attempt

        :param connection: Connection attempting to connect
        :param connectMessage: Message content attempting to connect
        :return:
        """
        # Not Implemented, only dummy for code auto complete
        pass
    @property
    def isRunning(self):
        """
        Whether or not the server is currently running
        :return: True if the server is running, false otherwise
        """
        return self.__isRunning

    @property
    def port(self):
        """
        :return: The local port that the server is running on
        """
        return self.__transport.port

    @property
    def clientCount(self):
        """
        :return: the number of clients currently connected to this server
        """
        return len(self.__clients)

    @property
    def timeoutTime(self):
        return self._defaultTimeout

    @timeoutTime.setter
    def timeoutTime(self, value: int):
        self._defaultTimeout = value
        for connection in self.__clients.values():
            connection.timeoutTime = self._defaultTimeout

    #region Message Handlers

    def registerMessageHandler(self, messageID: int, callback: Callable[[int, Message], None]):
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

    def changeTransport(self, newTransport: IServer):
        """
        Disconnects the client if it's connected and swaps out the transport it's using.

        This method does not automatically reconnect to the server. To continue communicating with the server,
        Connect() must be called again.

        :param newTransport: The new transport to use for sending and receiving data.
        :return:
        """
        self.stop()
        self.__transport = newTransport

    def start(self, port: int, maxClientCount: int):
        """
        Starts the server

        :param port: The local port on which to start the server
        :param maxClientCount: The maximum number of concurrent connections to allow
        :return:
        """
        self.stop()

        increaseActiveCount()
        #TODO: Get message handlers automatically from attributes ?
        self.__maxClientCount = maxClientCount
        self.__pendingConnections = []
        self.__clients = {}
        self.__timedOutClients = []
        self.__initializeClientIDs()

        self.subToTransportEvents()
        self.__transport.start(port)

        self.startTime()
        self.heartbeat()

        self.__isRunning = True
        logger.info("Started on port {}".format(port))

    def subToTransportEvents(self):
        """
        Subscribes appropriate methods to the transport's events.
        :return:
        """
        self.__transport.Connected += self.handleConnectionAttempt
        self.__transport.DataReceived += self._handleData
        self.__transport.Disconnected += self.transportDisconnected

    def unsubFromTransportEvents(self):
        """
        Unsubscribes methods from all the transport's events.
        :return:
        """
        self.__transport.Connected -= self.handleConnectionAttempt
        self.__transport.DataReceived -= self._handleData
        self.__transport.Disconnected -= self.transportDisconnected

    def handleConnectionAttempt(self, connection: Connection):
        """
        Handles an incoming connection attempt

        :param connection: incoming connection attempt
        :return:
        """
        connection.initialize(self, self._defaultTimeout)

    def handleConnect(self, connection: Connection, connectMessage: Message):
        """
        Handles a connect message

        :param connection: The client that sent the connect message
        :param connectMessage: The connect message
        :return:
        """
        connection.setPending()

        if self.handleConnection is None:
            self.acceptConnection(connection)
        elif self.clientCount < self.__maxClientCount:
            if connection not in self.__clients.values() and connection not in self.__pendingConnections:
                self.__pendingConnections.append(connection)
                self.send(createMessage(MessageHeader.Connect), connection)
                self.handleConnection(connection, connectMessage)
            else:
                self.__reject(connection, RejectReason.AlreadyConnected)
        else:
            self.__reject(connection, RejectReason.ServerFull)

    def accept(self, connection: Connection):
        """
        Accepts the given pending connection

        :param connection: The connection to accept
        :return:
        """
        if connection in self.__pendingConnections:
            self.__pendingConnections.remove(connection)
            self.acceptConnection(connection)
        else:
            logger.warning("Couldn't accept connection from {} because no such connection was pending!".format(connection))

    def reject(self, connection: Connection, message: Message = None):
        """
        Rejects the given pending connection

        :param connection: The connection to reject
        :param message: Data that should be sent to the client being rejected. Use message.createInternal() to get an empty message instance
        :return:
        """
        if message is not None and message.readBits != 0:
            logger.error("Use the parameterless 'Message.Create()' overload when setting rejection data!")

        if connection in self.__pendingConnections:
            self.__pendingConnections.remove(connection)
            self.__reject(connection, RejectReason.Rejected, message)
        else:
            logger.warning(
                "Couldn't accept connection from {} because no such connection was pending!".format(connection))

    def acceptConnection(self, connection: Connection):
        """
        Checks if the given connection can be accepted, and accepts the connection if possible.

        :param connection: The connection to accept
        """
        if self.clientCount < self.__maxClientCount:
            if connection not in self.__clients:
                clientID = self.getAvailableClientId()
                connection.id = clientID
                self.__clients[clientID] = connection
                connection.resetTimeout()
                connection.sendWelcome()
            else:
                self.__reject(connection, RejectReason.AlreadyConnected)
        else:
            self.__reject(connection, RejectReason.ServerFull)


    def __reject(self, connection: Connection, reason: Union[RejectReason, int], rejectMessage: Message = None):
        """
        Rejects the given pending connection

        :param connection: The connection to reject
        :param reason: The reason why the connection is being rejected
        :param rejectMessage: Data that should be sent to the client being rejected.
        Use message.createInternal() to get an empty message instance
        :return:
        """
        if reason != RejectReason.AlreadyConnected:
            # Sending a reject message about the client already being connected could theoretically be exploited to
            # obtain information on other connected clients, although in practice that seems very unlikely.
            # However, under normal circumstances, clients should never actually encounter a scenario
            # where they are "already connected".
            message = createMessage(MessageHeader.Reject)
            message.putUInt8(reason)

            if reason == RejectReason.Custom:
                message.appendMessage(rejectMessage)

            for i in range(3): # riptide sends the reject message 3 times see server.cs ln 271
                connection.sendMessage(message, False)
            message.release()
        connection.resetTimeout()
        connection.localDisconnect()
        #self.__transport.close(connection)

        logger.info("Rejected connection from {}: {}.".format(connection, rejectReasonToString(reason)))

    def heartbeat(self):
        """
        Checks if clients have timed out

        :return:
        """
        for connection in self.__clients.values():
            if connection.hasTimedOut:
                self.__timedOutClients.append(connection)

        for connection in self.__pendingConnections:
            if connection.hasConnectAttemptTimedOut:
                self.__timedOutClients.append(connection)

        for connection in self.__timedOutClients:
            self.localDisconnect(connection, DisconnectReason.TimedOut)

        self.__timedOutClients.clear()

        self.executeLater(self.heartbeat_interval, HeartbeatEvent(priority=self.heartbeat_interval + self.current_time,
                                                                  peer=self))

    def update(self):
        """
        Handles any received messages and invokes any delayed events which need to be invoked.

        :return:
        """
        super(Server, self).update()
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
            self.onMessageReceived(message, connection)
        elif header == MessageHeader.Ack:
            connection.handleAck(message)
        elif header == MessageHeader.Connect:
            self.handleConnect(connection, message)
        elif header == MessageHeader.Heartbeat:
            connection.handleHeartbeat(message)
        elif header == MessageHeader.Disconnect:
            self.localDisconnect(connection, DisconnectReason.Disconected)
        elif header == MessageHeader.Welcome:
            if connection.handleWelcomeResponse(message):
                self.onClientConnected(connection)
        else:
            logger.warning("Unexpected message header '{}'! Discarding message received from {}.".format(header, connection))
        message.release()

    def send(self, message: Message, toClient: Union[int, Connection], shouldRelease: bool = True) -> int:
        """
        Sends a message to a given client

        :param message: The message to send
        :param toClient: Either the numeric ID of or the connection to the client to send the message to
        :param shouldRelease: Whether or not to return the message to the pool after it is sent. Defaults to True
        :return:
        """
        if isinstance(toClient, int):
            if toClient in self.__clients:
                toClient = self.__clients[toClient]
            else:
                logger.debug("Attempted to send to non-existing client: '{}'".format(toClient))
                return 0

        return toClient.sendMessage(message, shouldRelease)

    def sendToAll(self, message: Message, exceptToClientId: int = -1, shouldRelease: bool = True):
        """
        Sends a message to all connected clients

        :param message: The message to send
        :param exceptToClientId: The numeric ID of the client to not send the message to. Defaults to < 0 (= send to all clients)
        :param shouldRelease: Whether or not to return the message to the pool after it is sent. Defaults to True
        :return:
        """
        if exceptToClientId < 0:
            for client in self.__clients.values():
                client.sendMessage(message, False)
        else:
            for client in self.__clients.values():
                if client.id != exceptToClientId:
                    client.sendMessage(message, False)

        if shouldRelease:
            message.release()

    def tryGetClient(self, id: int) -> Tuple[bool, Optional[Connection]]:
        """
        Retrieves the client with the given ID, if a client with that ID is currently connected.

        :param id: The ID of the client to retriev
        :return: True if success, False otherwise. If successful, also returns the client.
        Otherwise the second return value is None
        """
        if id not in self.__clients:
            return False, None
        return True, self.__clients[id]

    def disconnectClient(self, client: Union[int, Connection], message: Message = None):
        """
        Disconnects the given client

        :param client: The client to disconnect
        :param message: Data that should be sent to the client being disconnected.
        Use message.createInternal() to get an empty message instance
        :return:
        """
        if message is not None and message.readBits != 0:
            logger.error("Use the parameterless 'Message.Create()' overload when setting disconnection data!")

        if isinstance(client, int):
            result, client = self.tryGetClient(client)
        else:
            result = True
        if result:
            self.sendDisconnect(client, DisconnectReason.Kicked, message)
            self.localDisconnect(client, DisconnectReason.Kicked)
        else:
            logger.warning("Could not disconnect client '{}' because it was not connected !".format(id))

    def disconnect(self, connection: "Connection", reason: Union[DisconnectReason, int]):
        if connection.isConnected and connection.canQualityDisconnect:
            self.localDisconnect(connection, reason)

    def localDisconnect(self, client: Connection, reason: Union[DisconnectReason, int]):
        """
        Cleans up the local side of the given connection

        :param client: The client to disconnect
        :param reason: The reason why the client is being disconnected
        :return:
        """
        if client.peer != self:
            logger.warning("Attempted to disconnect Client from server {}, but client belongs to server {}".format(self, client.peer))
            return # Client does not belong to this server
        self.__transport.close(client)

        if client.id in self.__clients:
            del self.__clients[client.id]
            self.__availableClientIDs.append(client.id)
        
        if client.isConnected:
            self.onClientDisconnected(client, reason)
        elif client.isPending:
            self.onConnectionFailed(client)

        client.localDisconnect()

    def transportDisconnected(self, connection: Connection, reason: Union[DisconnectReason, int]):
        """
        What to do when the transport disconnects a client
        """
        self.localDisconnect(connection, reason)

    def stop(self):
        """
        Stops the server
        :return:
        """
        if not self.isRunning:
            return

        self.__pendingConnections.clear()
        disconnectBytes = [MessageHeader.Disconnect, DisconnectReason.ServerStopped]
        for client in self.__clients.values():
            client.send(disconnectBytes, len(disconnectBytes))
        self.__clients.clear()

        self.__transport.shutdown()
        self.unsubFromTransportEvents()

        decreaseActiveCount()

        self.stopTime()
        self.__isRunning = False
        logger.info("Server Stopped")

    def __initializeClientIDs(self):
        """
        Initializes available client IDs
        :return:
        """
        if self.__maxClientCount > (2**16) - 1:
            raise Exception("A server's max client count may not exceed {} !".format((2**16)-1))

        self.__availableClientIDs = list(range(1, self.__maxClientCount+1))

    def getAvailableClientId(self) -> int:
        """
        Retrieves an available client ID.

        :return: The client ID. 0 if none were available.
        """
        if len(self.__availableClientIDs) > 0:
            return self.__availableClientIDs.pop(0)
        logger.error("No available client IDs, assigned 0!")
        return 0

    #region Messages
    def sendDisconnect(self, client: Connection, reason: Union[DisconnectReason, int], disconnectMessage: Message = None):
        """
        Sends a disconnect message.

        :param client: The client to send the disconnect message to
        :param reason: Why the client is being disconnected
        :param disconnectMessage: Optional custom data that should be sent to the client being disconnected
        :return:
        """
        message = createMessage(MessageHeader.Disconnect)
        message.putUInt8(reason)
        if reason == DisconnectReason.Kicked and disconnectMessage is not None:
            message.appendMessage(disconnectMessage)

        self.send(message, client)

    def sendClientConnected(self, newClient: Connection):
        """
        Sends a client connected message

        :param newClient: The newly connected client
        :return:
        """
        message = createMessage(MessageHeader.ClientConnected)
        message.putUInt16(newClient.id)

        self.sendToAll(message, exceptToClientId=newClient.id)

    def sendClientDisconnected(self, id: int):
        """
        Sends a client disconnected message

        :param id: The numeric ID of the client that disconnected
        :return:
        """
        message = createMessage(MessageHeader.ClientDisconnected)
        message.putUInt16(id)

        self.sendToAll(message)

    #endregion

    #region Event Handlers
    def onClientConnected(self, client: Connection):
        """
        Invokes the ClientConnected event.

        :param client: The newly connected client.
        :return:
        """
        logger.info("Client '{}' ({}) connected Successfully !".format(client.id, client))
        self.sendClientConnected(client)
        self.ClientConnected(client)

    def onConnectionFailed(self, client):
        logger.info("Connection {} stopped responding before the connection was fully established")
        self.ConnectionFailed(client)

    def onMessageReceived(self, message: Message, connection: Connection):
        """
        Invokes the MessageReceived event and initiates handling of the received message.

        :param message: The received message
        :param connection: The client from which the message was received
        :return:
        """
        messageID = message.msgID
        if self.messageRelayFilter is not None and self.messageRelayFilter.shouldRelay(messageID):
            self.sendToAll(message, connection.id)
            return

        self.MessageReceived(connection, messageID, message)

        if messageID in self.__messageHandlers:
            self.__messageHandlers[messageID](connection.id, message)
        else:
            logger.warning("No message handler method found for message ID {}!".format(messageID))

    def onClientDisconnected(self, client: Connection, reason: Union[DisconnectReason, int]):
        """
        Invokes the ClientDisconnected event.

        :param client: The client that disconnected
        :param reason: The reason for the disconnection
        :return:
        """
        self.sendClientDisconnected(client.id)

        logger.info("Client {} ({}) disconnected: {}.".format(client.id, client, disconnectReasonToString(reason)))
        self.ClientDisconnected(client, reason)
    #endregion
