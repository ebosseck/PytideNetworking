from time import sleep

from pytidenetworking.message import Message, create
from pytidenetworking.message_base import MessageSendMode
from pytidenetworking.server import Server
from pytidenetworking.threading.fixedupdatethreads import FixedUpdateThread
from pytidenetworking.transports.tcp.tcp_server import TCPServer

PORT = 7777

MESSAGE_ID_BOOL = 0
MESSAGE_ID_BOOL_ARRAY = 1

MESSAGE_ID_BYTE = 2
MESSAGE_ID_BYTE_ARRAY = 3
MESSAGE_ID_SBYTE = 4
MESSAGE_ID_SBYTE_ARRAY = 5

MESSAGE_ID_SHORT = 6
MESSAGE_ID_SHORT_ARRAY = 7
MESSAGE_ID_USHORT = 8
MESSAGE_ID_USHORT_ARRAY = 9

MESSAGE_ID_INT = 10
MESSAGE_ID_INT_ARRAY = 11
MESSAGE_ID_UINT = 12
MESSAGE_ID_UINT_ARRAY = 13

MESSAGE_ID_LONG = 14
MESSAGE_ID_LONG_ARRAY = 15
MESSAGE_ID_ULONG = 16
MESSAGE_ID_ULONG_ARRAY = 17

MESSAGE_ID_FLOAT = 18
MESSAGE_ID_FLOAT_ARRAY = 19

MESSAGE_ID_DOUBLE = 20
MESSAGE_ID_DOUBLE_ARRAY = 21

MESSAGE_ID_STRING = 22
MESSAGE_ID_STRING_ARRAY = 23

MESSAGE_SEND_MODE = MessageSendMode.Unreliable

def runServer():
    tcpTransport = TCPServer()
    server: Server = Server(tcpTransport)
    server.start(PORT, 10)

    serverUpdater: FixedUpdateThread = FixedUpdateThread(server.update)
    serverUpdater.start()

    return server


def handleBool(client: int, message: Message):
    value = message.getBool()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_BOOL)
    message.putBool(value)
    server.send(message, client)

def handleBoolArray(client: int, message: Message):
    value = message.getBoolArray()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_BOOL_ARRAY)
    message.putBoolArray(value)
    server.send(message, client)


def handleByte(client: int, message: Message):
    value = message.getUInt8()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_BYTE)
    message.addByte(value)
    server.send(message, client)

def handleByteArray(client: int, message: Message):
    value = message.getUInt8Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_BYTE_ARRAY)
    message.addByteArray(value)
    server.send(message, client)

def handleSByte(client: int, message: Message):
    value = message.getInt8()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_SBYTE)
    message.addSByte(value)
    server.send(message, client)

def handleSByteArray(client: int, message: Message):
    value = message.getInt8Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_SBYTE_ARRAY)
    message.addSByteArray(value)
    server.send(message, client)

def handleShort(client: int, message: Message):
    value = message.getInt16()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_SHORT)
    message.addShort(value)
    server.send(message, client)

def handleShortArray(client: int, message: Message):
    value = message.getInt16Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_SHORT_ARRAY)
    message.addShortArray(value)
    server.send(message, client)

def handleUShort(client: int, message: Message):
    value = message.getUInt16()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_USHORT)
    message.addUShort(value)
    server.send(message, client)

def handleUShortArray(client: int, message: Message):
    value = message.getUInt16Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_USHORT_ARRAY)
    message.addUShortArray(value)
    server.send(message, client)


def handleInt(client: int, message: Message):
    value = message.getInt32()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_INT)
    message.addInt(value)
    server.send(message, client)

def handleIntArray(client: int, message: Message):
    value = message.getInt32Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_INT_ARRAY)
    message.addIntArray(value)
    server.send(message, client)

def handleUInt(client: int, message: Message):
    value = message.getUInt32()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_UINT)
    message.addUInt(value)
    server.send(message, client)

def handleUIntArray(client: int, message: Message):
    value = message.getUInt32Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_UINT_ARRAY)
    message.addUIntArray(value)
    server.send(message, client)


def handleLong(client: int, message: Message):
    value = message.getInt64()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_LONG)
    message.addLong(value)
    server.send(message, client)

def handleLongArray(client: int, message: Message):
    value = message.getInt64Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_LONG_ARRAY)
    message.addLongArray(value)
    server.send(message, client)

def handleULong(client: int, message: Message):
    value = message.getUInt64()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_ULONG)
    message.addULong(value)
    server.send(message, client)

def handleULongArray(client: int, message: Message):
    value = message.getUInt64Array()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_ULONG_ARRAY)
    message.addULongArray(value)
    server.send(message, client)

def handleFloat(client: int, message: Message):
    value = message.getFloat()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_FLOAT)
    message.addFloat(value)
    server.send(message, client)

def handleFloatArray(client: int, message: Message):
    value = message.getFloatArray()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_FLOAT_ARRAY)
    message.addFloatArray(value)
    server.send(message, client)

def handleDouble(client: int, message: Message):
    value = message.getDouble()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_DOUBLE)
    message.addDouble(value)
    server.send(message, client)

def handleDoubleArray(client: int, message: Message):
    value = message.getDoubleArray()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_DOUBLE_ARRAY)
    message.addDoubleArray(value)
    server.send(message, client)

def handleString(client: int, message: Message):
    value = message.getString()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_STRING)
    message.addString(value)
    server.send(message, client)

def handleStringArray(client: int, message: Message):
    value = message.getStringArray()
    print("Received Message with content: '{}' from Client {}".format(value, client))

    message = create(MESSAGE_SEND_MODE, MESSAGE_ID_STRING_ARRAY)
    message.addStringArray(value)
    server.send(message, client)


if __name__ == "__main__":
    server = runServer()
    server.registerMessageHandler(MESSAGE_ID_BOOL, handleBool)
    server.registerMessageHandler(MESSAGE_ID_BOOL_ARRAY, handleBoolArray)

    server.registerMessageHandler(MESSAGE_ID_BYTE, handleByte)
    server.registerMessageHandler(MESSAGE_ID_BYTE_ARRAY, handleByteArray)
    server.registerMessageHandler(MESSAGE_ID_SBYTE, handleSByte)
    server.registerMessageHandler(MESSAGE_ID_SBYTE_ARRAY, handleSByteArray)

    server.registerMessageHandler(MESSAGE_ID_SHORT, handleShort)
    server.registerMessageHandler(MESSAGE_ID_SHORT_ARRAY, handleShortArray)
    server.registerMessageHandler(MESSAGE_ID_USHORT, handleUShort)
    server.registerMessageHandler(MESSAGE_ID_USHORT_ARRAY, handleUShortArray)

    server.registerMessageHandler(MESSAGE_ID_INT, handleInt)
    server.registerMessageHandler(MESSAGE_ID_INT_ARRAY, handleIntArray)
    server.registerMessageHandler(MESSAGE_ID_UINT, handleUInt)
    server.registerMessageHandler(MESSAGE_ID_UINT_ARRAY, handleUIntArray)

    server.registerMessageHandler(MESSAGE_ID_LONG, handleLong)
    server.registerMessageHandler(MESSAGE_ID_LONG_ARRAY, handleLongArray)
    server.registerMessageHandler(MESSAGE_ID_ULONG, handleULong)
    server.registerMessageHandler(MESSAGE_ID_ULONG_ARRAY, handleULongArray)

    server.registerMessageHandler(MESSAGE_ID_FLOAT, handleFloat)
    server.registerMessageHandler(MESSAGE_ID_FLOAT_ARRAY, handleFloatArray)

    server.registerMessageHandler(MESSAGE_ID_DOUBLE, handleDouble)
    server.registerMessageHandler(MESSAGE_ID_DOUBLE_ARRAY, handleDoubleArray)

    server.registerMessageHandler(MESSAGE_ID_STRING, handleString)
    server.registerMessageHandler(MESSAGE_ID_STRING_ARRAY, handleStringArray)

    while(True):
        sleep(1)