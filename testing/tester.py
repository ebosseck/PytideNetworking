from pytidenetworking.message import Message
from pytidenetworking.utils import converter as conv


if __name__ == "__main__":
    values = [0xff] * 2

    for i in range(16):
        result = conv.setBitsFromBytes(values, i+1, [0x0] * 3, 4)
        print(' '.join([bin((~a)&0xff) for a in result]))

    #value = [True, False, True, False, False, True, True, True, False]
    #message = Message()
    #message.init()
    #print("A")
    #message.putBoolArray(value)
    #print("B")
    #readValue = message.getBoolArray()
    #print("C")