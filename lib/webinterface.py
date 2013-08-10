import re

import jinja2

from lib.http import Response
from settings import WEBINTERFACE_URI


# closurized dict mapping RegExes to functions
views = {}


# closurized Jinja2 Environment
env = jinja2.Environment(
    loader=jinja2.PackageLoader('webinterface', 'templates'),
    autoescape=True)
env.globals['base_url'] = '/%s/' % WEBINTERFACE_URI


class HttpError(Exception):
    def build_response(self):
        return Response(content=self.message, status_code=self.status_code)


class Http401Error(HttpError):
    """ If client has to authenticate itsself to see the website. """
    def __init__(self, realm, msg=''):
        self.realm = realm
        HttpError.__init__(self, msg if msg else '401 - Unauthorized')

    def build_response(self):
        r = Response(content=self.message, status_code=401)
        r.set_header('WWW-Authenticate', 'Basic realm="%s"' % self.realm)
        return r


class Http404Error(HttpError):
    def __init__(self, msg=''):
        self.status_code = 404
        HttpError.__init__(self, msg if msg else '404 - Not Found')


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
            try:
                response = wrap_response(function(req, *match.groups()))
            except HttpError as e:
                response = e.build_response()
            break
    return response
