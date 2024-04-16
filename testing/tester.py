from pytidenetworking.message import Message
from pytidenetworking.utils import converter as conv


def printBin(values):
    print(' '.join([format(a, '08b') for a in values]))

if __name__ == "__main__":
    values = [0xff] * 10
    printBin(values)
    for i in range(8):
        values = [0xff] * 10
        conv.setBitsFromBytes([0], 8, values, 16 + i)
        printBin(values)

    for i in range(8):
        values = [0] * 10
        conv.setBitsFromBytes([0xff], 8, values, 16 + i)
        printBin(values)


    for i in range(8):
        values = [0] * 10
        conv.setBitsFromBytes([0xff], 6, values, 16 + i)
        printBin(values)

    for i in range(8):
        values = [0] * 10
        conv.setBitsFromBytes([0xff], 4, values, 16 + i)
        printBin(values)

    for i in range(8):
        values = [0] * 10
        conv.setBitsFromBytes([0xff], 2, values, 16 + i)
        printBin(values)

    #for i in range(16):
    #    result = conv.setBitsFromBytes(values, i+1, [0x0] * 3, 4)
    #    print(' '.join([bin((~a)&0xff) for a in result]))

    #value = [True, False, True, False, False, True, True, True, False]
    #message = Message()
    #message.init()
    #print("A")
    #message.putBoolArray(value)
    #print("B")
    #readValue = message.getBoolArray()
    #print("C")