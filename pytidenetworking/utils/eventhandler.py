from typing import Callable


class EventHandler:
    """
    Basic event handler (similar to C#'s built in event handler)
    """
    def __init__(self):
        """
        Initializes the event handler
        """
        self.eventHandlers = []

    def addEventHandler(self, handler: Callable):
        """Register a new Event Handler"""

        self.eventHandlers.append(handler)

    def removeEventHandler(self, handler: Callable):
        """Remove an Event Handler"""
        if handler in self.eventHandlers:
            self.eventHandlers.remove(handler)

    def __iadd__(self, other: Callable):
        self.addEventHandler(other)
        return self

    def __isub__(self, other: Callable):
        self.removeEventHandler(other)
        return self

    def __len__(self):
        return len(self.eventHandlers)

    def __call__(self, *args, **kwargs):
        # TODO: Basic checks on all required arguments ?
        for handler in self.eventHandlers:
            handler(*args, **kwargs)