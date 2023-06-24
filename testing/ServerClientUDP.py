from time import sleep

from pytidenetworking import message
from pytidenetworking.client import Client
from pytidenetworking.message import Message, create as createMessage
from pytidenetworking.message_base import MessageSendMode
from pytidenetworking.server import Server
from pytidenetworking.threading.fixedupdatethreads import FixedUpdateThread
from pytidenetworking.transports.tcp.tcp_client import TCPClient
from pytidenetworking.transports.tcp.tcp_server import TCPServer
from pytidenetworking.transports.udp.udp_client import UDPClient
from pytidenetworking.transports.udp.udp_server import UDPServer

PORT = 7777

MESSAGE_ID_HANDLED = 42

def runServer():
    udpTransport = UDPServer()
    server: Server = Server(udpTransport)
    server.start(PORT, 10)

    serverUpdater: FixedUpdateThread = FixedUpdateThread(server.update)
    serverUpdater.start()

    return server

def connectClient():
    udpTransport = UDPClient()
    client: Client = Client(udpTransport)
    client.connect(("127.0.0.1", PORT))

    clientUpdater: FixedUpdateThread = FixedUpdateThread(client.update)
    clientUpdater.start()

    return client

def serverHandleMessage(val: int, rcvMsg: Message):
    print("Received Message with content: '{}' from Client {}".format(rcvMsg.getString(), val))
    msg = message.create(MessageSendMode.Reliable, MESSAGE_ID_HANDLED)
    msg.putString("Hello World !")
    server.sendToAll(msg)

def clientHandleMessage(message: Message):
    print("Received Message with content: '{}' from Server".format(message.getString()))

if __name__ == "__main__":
    server = runServer()
    server.registerMessageHandler(MESSAGE_ID_HANDLED, serverHandleMessage)

    sleep(1)
    client = connectClient()
    client.registerMessageHandler(MESSAGE_ID_HANDLED, clientHandleMessage)

    sleep(1)
    msg = message.create(MessageSendMode.Reliable, MESSAGE_ID_HANDLED)
    msg.putString("Hello World !")
    client.send(msg)

    while(True):
        sleep(1)