""" Event system. Able to call multiple event handlers on one event. """
from libmproxy import controller

from settings import LOCKED_MODE


# closurized events dictionary
events = {}


class EventPropagationStop(Exception):
    pass


class subscribe(object):
    """ Event subscription decorator. """

    def __init__(self, event, enable_when_locked=True):
        self.event = event
        self.enable_when_locked = enable_when_locked

    def __call__(self, function):
        if self.enable_when_locked or not LOCKED_MODE:
            events.setdefault(self.event, []).append(function)
        return function


class EventController(controller.Master):
    """ Waits for hooks sent by the server and propagates them to all event
        listeners. Events will be executed in the order they subscribed to the
        event. """
    def __init__(self, server):
        controller.Master.__init__(self, server)

    def run(self):
        try:
            return controller.Master.run(self)
        except KeyboardInterrupt:
            self.shutdown()

    def call(self, event, msg):
        """ Calls event with message parameter. """
        try:
            for function in events.get(event, []):
                r = function(msg)
                if r:
                    msg = r
        except EventPropagationStop:
            pass
        return msg

    def handle(self, msg):
        msg = self.call(msg.__class__.__name__.lower(), msg)
        msg.reply()
