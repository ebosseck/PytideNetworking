# Updated to 2.1.0


class DelayedEvent:
    """
    base delayed event prepared for use in priority queue
    """
    def __init__(self, priority: int):
        """
        Initializes the event

        :param priority: Priority of the event
        """
        self.priority = priority

    def __call__(self, *args, **kwargs):
        """Execute the event"""
        pass

    def __lt__(self, other):
        """Compare the priority of the event"""
        return self.priority < other.priority