""" Event system. Able to call multiple event handlers on one event.
    Currently used events: request, response, db_init. """
import logging

import lib.utils

from libmproxy import controller


logger = logging.getLogger(__name__)


# closurized events dictionary
events = {}


class EventPropagationStop(Exception):
    pass


class subscribe(object):
    """ Event subscription decorator. """

    def __init__(self, event, mode='*'):
        self.event = event
        self.enabled = lib.utils.resolve_mode(mode)

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

    def handle(self, msg):
        """ Handles internal controller event and distributes it to all
            subscribed listeners. """
        try:
            call(msg.__class__.__name__.lower(), msg)
            msg.reply()
        except Exception as e:
            logger.exception(e)


def call(event, *args):
    """ Calls events with arbitrary parameters. """
    for function in events.get(event, []):
        try:
            function(*args)
        except EventPropagationStop:
            break
        except Exception as e:
            logger.exception(e)
