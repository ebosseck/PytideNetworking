import random
import unittest

import pytidenetworking.utils.converter as conv

RANDOM_TEST_COUNT = 1000000

class ValueConversionTests(unittest.TestCase):

    #region ZigZag
    def testZigZag32(self):
        #Specific test cases
        test_values = [0, -1, 1, 100, -100, 2**16]

        for val in test_values:
            encoded = conv.zigzagEncode(val, 32)
            decoded = conv.zigzagDecode(encoded)
            if val != decoded:
                print("Coding error: {} != {} (encoded as {})".format(val, decoded, encoded))
            self.assertEqual(val, decoded)

        # random values, for completeness
        test_values = randomListInt(RANDOM_TEST_COUNT, -2**31, 2**31)
        for val in test_values:
            encoded = conv.zigzagEncode(val, 32)
            decoded = conv.zigzagDecode(encoded)
            if val != decoded:
                print("Coding error: {} != {} (encoded as {})".format(val, decoded, encoded))
            self.assertEqual(val, decoded)

    def testZigZag64(self):
        test_values = [0, -1, 1, 100, -100, 2 ** 16]

        for val in test_values:
            encoded = conv.zigzagEncode(val, 64)
            decoded = conv.zigzagDecode(encoded)
            if val != decoded:
                print("Coding error: {} != {} (encoded as {})".format(val, decoded, encoded))
            self.assertEqual(val, decoded)

        # random values, for completeness
        test_values = randomListInt(RANDOM_TEST_COUNT, -2**63, 2**63)
        for val in test_values:
            encoded = conv.zigzagEncode(val, 64)
            decoded = conv.zigzagDecode(encoded)
            if val != decoded:
                print("Coding error: {} != {} (encoded as {})".format(val, decoded, encoded))
            self.assertEqual(val, decoded)
    #endregion

    #region SetBits & GetBits
    def testSetBits(self):
        result = [0, 0, 0, 0]
        components = [(0b0101, 4), (0b11111111_00000000, 16), (0b1111, 4), (0b01, 2)]
        expected = [0b00000101, 0b11110000, 0b11111111, 0b01]

        self.evalSetBits(result, components, expected)

        result = [0b11111111, 0b11111111, 0b11111111, 0b11111111]
        components = [(0b0101, 4), (0b11111111_00000000, 16), (0b1111, 4), (0b01, 2)]
        expected = [0b00000101, 0b11110000, 0b11111111, 0b11111101]

        self.evalSetBits(result, components, expected)

        result = [0, 0, 0, 0, 0]
        components = [(0b01, 2), (0b1_11111110_00000001, 17), (0b10, 2)]
        expected = [0b00000101, 0b11111000, 0b00010111, 0, 0]

        self.evalSetBits(result, components, expected)

        result = [0xff, 0xff, 0xff, 0xff, 0xff]
        components = [(0b01, 2), (0b1_11111110_00000001, 17), (0b10, 2)]
        expected = [0b00000101, 0b11111000, 0b11110111, 0xff, 0xff]

        self.evalSetBits(result, components, expected)

    def evalSetBits(self, result, components, expected):
        bit_counter = 0
        for component, bitcount in components:
            conv.setBits(component, bitcount, result, bit_counter)
            bit_counter += bitcount

        self.assertEqual(result, expected)

    def testGetBits(self):
        components = randomListIntTuple(RANDOM_TEST_COUNT, 0, 2**64, 1, 64)
        self.evalGetBits(components)

        components = randomListIntTuple(RANDOM_TEST_COUNT, 0, 2 ** 32, 1, 32)
        self.evalGetBits(components)

    def evalGetBits(self, components):
        bitcount = 0
        for c in components:
            bitcount += c[1]
        bytecount = bitcount // 8 + 9

        tmp = [0] * bytecount
        expected = []
        bit_counter = 0
        for component, bitcount in components:
            conv.setBits(component, bitcount, tmp, bit_counter)
            bit_counter += bitcount
            expected.append((component & (2 ** bitcount) - 1, bitcount))

        result = []

        bit_counter = 0
        for _, bitcount in components:
            readbits = conv.getBits(bitcount, tmp, bit_counter)
            bit_counter += bitcount
            result.append((readbits, bitcount))

        self.assertEqual(result, expected)
    #endregion

    #region VarULong

    def testVarULong(self):
        test_values = range(0, 2**7)

        for val in test_values:
            ulong = conv.toVarULong(val)
            result, count = conv.fromVarULong(ulong, 0)
            self.assertEqual(result, val)

        test_values = range(-2**6, 2 ** 6)

        for val in test_values:
            zigzag = conv.zigzagEncode64(val)
            ulong = conv.toVarULong(zigzag)
            result, count = conv.fromVarULong(ulong, 0)
            self.assertEqual(conv.zigzagDecode(result), val)

        test_values = randomListInt(RANDOM_TEST_COUNT, 0, 2 ** 63)

        for val in test_values:
            ulong = conv.toVarULong(val)
            result, count = conv.fromVarULong(ulong, 0)
            self.assertEqual(result, val)

        test_values = randomListInt(RANDOM_TEST_COUNT, -2 ** 62, 2 ** 62)

        for val in test_values:
            zigzag = conv.zigzagEncode64(val)
            ulong = conv.toVarULong(zigzag)
            result, count = conv.fromVarULong(ulong, 0)
            self.assertEqual(conv.zigzagDecode(result), val)

    #endregion

    #region bytes to bits

    def testBytesToBits(self):
        result = [0] * 4
        expected = [0b10101010, 0b00110011, 0b11110000, 0b00111100]
        result = conv.bytesToBits(expected, result, 0)
        self.assertEqual(result, expected)

        result = [0] * 5
        expected = [0b10100000, 0b00111010, 0b00000011, 0b11001111, 0b00000011]
        value = [0b10101010, 0b00110011, 0b11110000, 0b00111100]
        result = conv.bytesToBits(value, result, 4)
        self.assertEqual(result, expected)

    def testBytesFromBits(self):
        for i in range(RANDOM_TEST_COUNT):
            bit = random.randint(0, 7)
            bytelen = random.randint(20, 20)
            expected = randomListInt(bytelen, 0, 255)
            tmpbits = [0] * (bytelen + 1)

            tmpbits = conv.bytesToBits(expected, tmpbits, bit)
            result = [0] * len(expected)
            result = conv.bytesFromBits(tmpbits, len(expected) * 8, bit)
            self.assertEqual(expected, list(result))

    def testSetBitsFromBytes(self):
        pass
    #region

#region Tools
def randomListInt(count, start, end):
    result = []
    for _ in range(count):
        result.append(random.randrange(start, end))
    return result

def randomListIntTuple(count, start, end, startA, endA):
    result = []
    for _ in range(count):
        result.append((random.randrange(start, end), random.randrange(startA, endA)))
    return result


def randomListFloat(count, start, end):
    result = []
    for _ in range(count):
        divisor = random.randrange(start, end)
        result.append(random.randrange(start, end) / float(0.01 if divisor == 0 else divisor))
    return result
#endregion
