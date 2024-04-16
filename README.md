# Pytide

Python port of [Riptide](https://github.com/RiptideNetworking/Riptide), a light weight networking library.

This port provides functionality for establishing connections with clients and servers using the Riptide protocol. 

## Compatibility

This port was last tested for functionality with Riptide [Commit 5a86ca0](https://github.com/RiptideNetworking/Riptide/tree/5a86ca0a67d6cce1fb080eaca0535d030528f0d6), Jan 26 2023

This port is compatible with Riptide 2.1.0 to 2.2.0.

The Compatibility can be tested by connecting the C# client provided in the unity folder with the server implemented in testing/serverTCPTest.py or testing/serverUDPTest.py

## Compatible libraries in other languages

- C#: [Riptide](https://github.com/RiptideNetworking/Riptide)
- Dart/Flutter: [Riptide Dart Port](https://github.com/JayKay135/Riptide-Dart-Port)

## Getting Started

The API is mostly identical to [Riptide](https://github.com/RiptideNetworking/Riptide).

### Installation

#### From Source

Clone this repository and copy the folder "pytidenetworking" into your working directory.

#### Poetry

In your poetry project use

poetry add git+https://github.com/ebosseck/PytideNetworking.git

to add this project as an external dependency.
This should already be sufficient to be able to use the PytideNetworking library in your poetry project.

### Create a new Server

For an UDP server:
```python
    server: Server = Server()
    server.start(PORT, 10)
```

For a TCP server:

```python
    tcpTransport = TCPServer()
    server: Server = Server(tcpTransport)
    server.start(PORT, 10)
```

In order to process the messages:

```python
    serverUpdater: FixedUpdateThread = FixedUpdateThread(server.update)
    serverUpdater.start()
```

Handling received messages:

```python
def handleMessage(clientID: int, message: Message):
    pass # your code here
    
server.registerMessageHandler(messageID, handleMessage)
```

### Create a new Client

For an UDP client:
```python
    client: Client = Client()
    client.connect((SERVER_ADDRESS, PORT))
```

For a TCP client:
```python
    tcpTransport = TCPClient()
    client: Client = Client(tcpTransport)
    client.connect((SERVER_ADDRESS, PORT))
```

In order to process the messages:

```python
    clientUpdater: FixedUpdateThread = FixedUpdateThread(client.update)
    clientUpdater.start()
```

Handling received messages:

```python
def handleMessage(message: Message):
    pass # your code here
    
client.registerMessageHandler(messageID, handleMessage)
```

### Send Messages

```python
    msg = message.create(MessageSendMode.Unreliable, MESSAGE_ID_HANDLED)
    msg.putString("Hello World !")
    client.send(msg)
```

For more details, also check out the documentation of Riptide, as well as the samples in the testing folder.

Furthermore, a low level documentation of the protocol used is available in docs/ as pdf.

## Low-Level Transports supported by Pytide

* UDP (built-in)
* TCP (built-in)

## License

Distributed under the MIT license. See LICENSE.md for more information. Copyright © 2023 [VISUS](https://www.visus.uni-stuttgart.de/en/), [University of Stuttgart](https://www.uni-stuttgart.de/)

This project is supported by [VISUS](https://www.visus.uni-stuttgart.de/en/), University of Stuttgart
