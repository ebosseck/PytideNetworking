from threading import Thread
from time import sleep, time
from typing import Callable


class FixedUpdateThread(Thread):
    """
    Utility class calling the given function in a fixed interval
    """

    def __init__(self, function: Callable[[], None], timestep=1/50.0):
        """
        Utility class calling the given function in a fixed interval

        :param function: The function to call
        :param timestep: The interval to call the function in seconds
        """
        super(FixedUpdateThread, self).__init__()
        self.shouldFinish = False
        self.function = function

        self.timestep = timestep

    def run(self) -> None:
        startTime = time()
        while not self.shouldFinish:
            self.function()

            sleepTime = (startTime + self.timestep) - time()
            if sleepTime > 0:
                sleep(sleepTime)
            startTime = time()

    def requestClose(self):
        """
        Request this thread to finish executing

        :return:
        """
        self.shouldFinish = True