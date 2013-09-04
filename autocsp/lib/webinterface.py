import re

import jinja2

from lib.http import status_codes, Response
from settings import WEBINTERFACE_URI


# closurized dict mapping RegExes to functions
views = {}


# closurized Jinja2 Environment
env = jinja2.Environment(
    loader=jinja2.PackageLoader('webinterface', 'templates'),
    autoescape=True)
env.globals['base_url'] = '/%s/' % WEBINTERFACE_URI


class HttpError(Exception):
    def __init__(self, status_code, msg=''):
        self.status_code = status_code
        msg = msg or '%d - %s' % (status_code, status_codes[status_code])
        Exception.__init__(self, msg)

    def build_response(self):
        return Response(content=self.message, status_code=self.status_code)


class Http400Error(HttpError):
    """ Client sent a bad request. """
    def __init__(self, msg=''):
        HttpError.__init__(self, 400, msg)


class Http401Error(HttpError):
    """ Client has to authenticate to view the website. """
    def __init__(self, realm, msg=''):
        self.realm = realm
        HttpError.__init__(self, msg if msg else '401 - Unauthorized')

    def build_response(self):
        r = Response(content=self.message, status_code=401)
        r.set_header('WWW-Authenticate', 'Basic realm="%s"' % self.realm)
        return r


class Http404Error(HttpError):
    def __init__(self, msg=''):
        HttpError.__init__(self, 404, msg)


class Http500Error(HttpError):
    def __init__(self, msg=''):
        HttpError.__init__(self, 500, msg)


class path(object):
    """ Path decorator. Maps a function to a URI RegEx. """
    def __init__(self, regex):
        self.path = re.compile('^%s$' % regex)

    def __call__(self, function):
        views[self.path] = function
        return function


def render_template(template, **kwargs):
    """ Wrapper for env.get_template. """
    return env.get_template(template).render(**kwargs)


def make_response(template, **kwargs):
    """ Makes a lib.http.Response from a template and its arguments. """
    return Response(content=render_template(template, **kwargs))


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
            except Exception as e:
                response = Http500Error().build_response()
                # TODO(qll): Implement logging
                print(e)
            break
    return response
