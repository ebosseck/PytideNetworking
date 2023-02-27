import unittest

from pytidenetworking.utils.eventhandler import EventHandler


class EventHandlerTests(unittest.TestCase):
    def test_something(self):
        event: EventHandler = EventHandler()

        self.eventDidRun = False
        event += self.event
        self.assertEqual(len(event), 1)
        self.assertEqual(False, self.eventDidRun)
        event(True)
        self.assertEqual(True, self.eventDidRun)
        event -= self.event

        self.assertEqual(len(event), 0)

    def event(self, value):
        self.eventDidRun = True
        self.assertEqual(True, value)

if __name__ == '__main__':
    unittest.main()
