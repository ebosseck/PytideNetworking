from typing import TypeVar, Generic, List

T = TypeVar('T')

class ObjectPool(Generic[T]):
    """
    Generic Object Pool
    """

    def __init__(self, size: int):
        """
        Initializes the object pool
        :param size: Size of the pool
        """
        self.size: int = size
        self.data: List[T] = []

    def createObject(self) -> T:
        """
        Dummy function. Override this with a factory function for the objects to be created
        :return:
        """
        return None

    def acquire(self) -> T:
        """
        Aquire an object from the pool, if the pool is empty, create a new Object

        :return: the object available for use
        """
        if len(self.data) > 0:
            return self.data.pop()
        else:
            return self.createObject()

    def release(self, object: T):
        """
        Releases the given object back into the pool. If the pool is already full, the object is destroyed
        :param object: Object to return
        :return:
        """
        if len(self.data) < self.size:
            self.data.append(object)
        else:
            del object

    def clearPool(self):
        """
        Clears all objects from the pool
        :return:
        """
        while len(self.data) > 0:
            del self.data[-1]