import math
import random
import unittest

from pytidenetworking.message import Message


class ValueSerialisationTests(unittest.TestCase):
    def testMessageBytes(self):

        bytes = b'ABCDEFG'

        message = Message()
        message.init()

        message.putBytes(bytes)
        readBytes = message.getBytes(len(bytes))

        self.assertEqual(bytes, readBytes)  # add assertion here

    def testMessageBool(self):
        value = True

        message = Message()
        message.init()

        message.putBool(value)
        readValue = message.getBool()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageBoolArray(self):
        value = [True, False, True, False, False, True, True, True, False]
        message = Message()
        message.init()
        message.putBoolArray(value)
        readValue = message.getBoolArray()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt8(self):

        value = -1

        message = Message()
        message.init()

        message.putInt8(value)
        readValue = message.getInt8()

        self.assertEqual(value, readValue)  # add assertion here

        value = 0xff

        message.init()

        message.putUInt8(value)
        readValue = message.getUInt8()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt8Array(self):

        value = list(range(-21, 21))

        message = Message()
        message.init()

        message.putInt8Array(value)
        readValue = message.getInt8Array()

        self.assertEqual(value, readValue)  # add assertion here

        value = list(range(42))

        message.init()

        message.putUInt8Array(value)
        readValue = message.getUInt8Array()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt16(self):

        value = 0x7fff

        message = Message()
        message.init()

        message.putInt16(value)
        readValue = message.getInt16()

        self.assertEqual(value, readValue)  # add assertion here

        value = 0xffff

        message.init()

        message.putUInt16(value)
        readValue = message.getUInt16()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt16Array(self):

        value = self.randomListInt(10, -2**14, 2**14)

        message = Message()
        message.init()
        message.putInt16Array(value)
        readValue = message.getInt16Array()

        self.assertEqual(value, readValue)  # add assertion here

        value = self.randomListInt(10, 0, 2**15)

        message.init()
        message.putUInt16Array(value)
        readValue = message.getUInt16Array()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt32(self):

        value = 0x7fff_ffff

        message = Message()
        message.init()

        message.putInt32(value)
        readValue = message.getInt32()

        self.assertEqual(value, readValue)  # add assertion here

        value = 0xffff_ffff

        message.init()

        message.putUInt32(value)
        readValue = message.getUInt32()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt32Array(self):

        value = self.randomListInt(10, -2**30, 2**30)

        message = Message()
        message.init()

        message.putInt32Array(value)
        readValue = message.getInt32Array()

        self.assertEqual(value, readValue)  # add assertion here

        value = self.randomListInt(10, 0, 2**31)

        message.init()

        message.putUInt32Array(value)
        readValue = message.getUInt32Array()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt64(self):

        value = 0x7fff_ffff_ffff_ffff

        message = Message()
        message.init()

        message.putInt64(value)
        readValue = message.getInt64()

        self.assertEqual(value, readValue)  # add assertion here

        value = 0xffff_ffff_ffff_ffff

        message = Message()
        message.init()

        message.putUInt64(value)
        readValue = message.getUInt64()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageInt64Array(self):

        value = self.randomListInt(10, -2**62, 2**62)

        message = Message()
        message.init()

        message.putInt64Array(value)
        readValue = message.getInt64Array()

        self.assertEqual(value, readValue)  # add assertion here

        value = self.randomListInt(10, 0, 2**63)

        message.init()

        message.putUInt64Array(value)
        readValue = message.getUInt64Array()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageFloat(self):

        value = math.pi

        message = Message()
        message.init()

        message.putFloat(value)
        readValue = message.getFloat()

        self.assertAlmostEqual(value, readValue, delta=0.000001)

    def testMessageFloatArray(self):

        value = self.randomListFloat(10, -100, 100)

        message = Message()
        message.init()

        message.putFloatArray(value)
        readValue = message.getFloatArray()

        for i in range(len(value)):
            self.assertAlmostEqual(value[i], readValue[i], delta=0.000001)

    def testMessageDouble(self):

        value = math.pi

        message = Message()
        message.init()

        message.putDouble(value)
        readValue = message.getDouble()

        self.assertAlmostEqual(value, readValue, delta=0.00000000001)

    def testMessageDoubleArray(self):

        value = self.randomListFloat(10, -100, 100)

        message = Message()
        message.init()

        message.putDoubleArray(value)
        readValue = message.getDoubleArray()

        for i in range(len(value)):
            self.assertAlmostEqual(value[i], readValue[i], delta=0.000001)

    def testMessageString(self):
        value = "Lorem ipsum in dolor sit amen"

        message = Message()
        message.init()

        message.putString(value)
        readValue = message.getString()

        self.assertEqual(value, readValue)  # add assertion here

    def testMessageStringArray(self):
        value = ["Lorem ipsum", " in dolor", " sit amen"]

        message = Message()
        message.init()

        message.putStringArray(value)
        readValue = message.getStringArray()

        self.assertEqual(value, readValue)  # add assertion here

    def randomListInt(self, count, start, end):
        result = []
        for _ in range(count):
            result.append(random.randrange(start, end))
        return result

    def randomListFloat(self, count, start, end):
        result = []
        for _ in range(count):
            divisor = random.randrange(start, end)
            result.append(random.randrange(start, end) / float(0.01 if divisor == 0 else divisor))
        return result
