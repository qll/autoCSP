import hashlib
import jinja2
import logging
import os
import re

import lib.csp
import lib.utils

from lib.http import status_codes, Response
from settings import ORIGIN, LOCKED_MODE, WEBINTERFACE_URI


# closurized dict mapping RegExes to functions
views = {}


# closurized Jinja2 Environment
env = jinja2.Environment(
    loader=jinja2.PackageLoader('webinterface', 'templates'),
    autoescape=True)
env.globals['base_url'] = '/%s/' % WEBINTERFACE_URI
env.globals['mode'] = 'locked' if LOCKED_MODE else 'learning'


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
        HttpError.__init__(self, 401)

    def build_response(self):
        r = Response(content=self.message, status_code=401)
        r.set_header('WWW-Authenticate', 'Basic realm="%s"' % self.realm)
        return r


class Http403Error(HttpError):
    def __init__(self, msg=''):
        HttpError.__init__(self, 403, msg)


class Http404Error(HttpError):
    def __init__(self, msg=''):
        HttpError.__init__(self, 404, msg)


class Http500Error(HttpError):
    def __init__(self, msg=''):
        HttpError.__init__(self, 500, msg)


class Redirect(Response):
    def __init__(self, location):
        Response.__init__(self, status_code=302)
        self.set_header('Location', location)


class csp(object):
    """ Defines a CSP for a view. """
    def __init__(self, csp):
        self.csp = {}
        for directive, uris in csp.items():
            for uri in uris:
                fulluri = uri % {'autocsp': '%s/%s' %
                                            (lib.utils.assemble_origin(ORIGIN),
                                             WEBINTERFACE_URI)}
                self.csp.setdefault(directive, []).append(fulluri)

    def __call__(self, function):
        key = ''
        for path, view in views.items():
            if view['function'] == function:
                key = path
                break
        if key:
            views[key]['csp'] = self.csp
        return function


class path(object):
    """ Path decorator. Maps a function to a URI RegEx. """
    def __init__(self, regex, mode='learning'):
        self.path = re.compile('^%s$' % regex)
        self.enabled = lib.utils.resolve_mode(mode)

    def __call__(self, function):
        if self.enabled and self.path not in views:
            views[self.path] = {'function': function}
        return function


def is_webinterface(path):
    """ Decides if URI is part of the webinterface given the path components.
    """
    return True if len(path) and path[0] == WEBINTERFACE_URI else False


def is_datasink(path):
    """ Checks if the path is part of the proxy's data sinks. """
    return is_webinterface(path) and len(path) > 1 and path[1] == '_'


def render_template(template, **kwargs):
    """ Wrapper for env.get_template. """
    return env.get_template(template).render(**kwargs)


def make_response(template, **kwargs):
    """ Makes a lib.http.Response from a template and its arguments. """
    return Response(content=render_template(template, **kwargs))


def wrap_response(val):
    """ Returns a lib.http.Response in any case. """
    return val if isinstance(val, Response) else Response(content=str(val))


def generate_token():
    """ Generates an unpredictable token or nonce. """
    return hashlib.sha256(os.urandom(32)).hexdigest()


def csrf(func):
    """ Decorator protecting a web ressource from CSRF. """
    def wrapper(*args):
        args = [i for i in args]
        cookies = args[0].get_cookies()
        if args[0].method == 'POST':
            params = args[0].get_form_urlencoded()
            if ('csrf' not in params or not cookies or not 'csrf' in cookies or
                params['csrf'][0] != cookies['csrf'][0]):
                # TODO(qll): invalidate CSRF token on failed attempts
                raise Http400Error('Invalid CSRF token.')
            cookies = None  # invalidate CSRF token
        if cookies and 'csrf' in cookies:
            token = cookies['csrf'][0]
        else:
            token = generate_token()
        args.append(token)
        response = func(*args)
        if not cookies:
            cookie = 'csrf=%s; Path=/%s/; HttpOnly' % (token, WEBINTERFACE_URI)
            response.headers['Set-Cookie'] = cookie
        return response
    return wrapper


def call_view(req, path):
    """ Selects a function with a matching RegEx and executes it. """
    response = Response(content='404 - Not Found', status_code=404)
    for regex, view in views.items():
        match = regex.match(path)
        if match:
            csp = {}
            try:
                response = wrap_response(view['function'](req, *match.groups()))
                if 'csp' in view:
                    csp = view['csp']
            except HttpError as e:
                response = e.build_response()
            except Exception as e:
                response = Http500Error().build_response()
                logging.getLogger(__name__).exception(e)
            response.set_header('Content-Security-Policy',
                                lib.csp.generate_policy(csp))
            break
    return response
