import re

import jinja2

from lib.http import Response


# closurized dict mapping RegExes to functions
views = {}


# closurized Jinja2 Environment
env = jinja2.Environment(loader=jinja2.PackageLoader('webinterface',
                                                     'templates'))


class path(object):
    """ Path decorator. Maps a function to a URI RegEx. """

    def __init__(self, regex):
        self.path = re.compile('^%s$' % regex)

    def __call__(self, function):
        views[self.path] = function
        return function


def make_response(template, **kwargs):
    """ Makes a lib.http.Response from a template and its arguments. """
    return Response(content=env.get_template(template).render(**kwargs))


def wrap_response(val):
    """ Returns a lib.http.Response in any case. """
    return val if isinstance(val, Response) else Response(content=str(val))


def call_view(req, path):
    """ Selects a function with a matching RegEx and executes it. """
    response = Response(content='404 - Not Found', status_code=404)
    for regex, function in views.items():
        match = regex.match(path)
        if match:
            response = wrap_response(function(req, *match.groups()))
            break
    return response
