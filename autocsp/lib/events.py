""" Event system. Able to call multiple event handlers on one event.
    Currently used events: request, response, db_init. """
import sys
import traceback

from libmproxy import controller

from settings import LOCKED_MODE


# closurized events dictionary
events = {}


class EventPropagationStop(Exception):
    pass


class subscribe(object):
    """ Event subscription decorator. """

    def __init__(self, event, mode='*'):
        self.event = event
        modes = ('*', 'locked', 'learning')
        if mode not in modes:
            raise ValueError('Event mode can only be one of the following: %s'
                             % modes)
        learn = True if mode in ('*', 'learning') else False
        locked = True if mode in ('*', 'locked') else False
        self.enabled = (LOCKED_MODE and locked) or (not LOCKED_MODE and learn)

    def __call__(self, function):
        if (self.enabled and (not (self.event in events
                                   and function in events[self.event]))):
            events.setdefault(self.event, []).append(function)
        return function


class EventController(controller.Master):
    """ Waits for hooks sent by the server and propagates them to all event
        listeners. Events will be executed in the order they subscribed to the
        event. """
    def __init__(self, server):
        controller.Master.__init__(self, server)

    def run(self):
        return controller.Master.run(self)

    def call(self, event, msg):
        """ Calls event with message parameter. """
        call(event, msg)

    def handle(self, msg):
        """ Handles internal controller event and distributes it to all
            subscribed listeners. """
        try:
            self.call(msg.__class__.__name__.lower(), msg)
            msg.reply()
        except Exception:
            # TODO(qll): implement logging
            _, e, tb = sys.exc_info()
            print('Error: %s' % e)
            print('Traceback:')
            traceback.print_tb(tb)
            del tb


def call(event, *args):
    """ Calls events with arbitrary parameters. """
    try:
        for function in events.get(event, []):
            function(*args)
    except EventPropagationStop:
        pass
