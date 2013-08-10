import base64
import re

import lib.http
import lib.webinterface

from lib.events import subscribe, EventPropagationStop
from settings import WEBINTERFACE_URI, WEBINTERFACE_AUTH


def is_webinterface(path):
    """ Decides if URI is part of the webinterface given the path components.
    """
    return True if len(path) and path[0] == WEBINTERFACE_URI else False


@subscribe('response', enable_when_locked=False)
def ignore_webinterface(response):
    if is_webinterface(response.request.get_path_components()):
        raise EventPropagationStop()


if WEBINTERFACE_AUTH:
    @subscribe('request', enable_when_locked=False)
    def handle_webinterface_auth(request):
        path = request.get_path_components()
        if is_webinterface(path):
            auth = base64.standard_b64encode('{0}:{1}'
                                             .format(*WEBINTERFACE_AUTH))
            if not re.match('^\s*Basic %s\s*$' % auth.replace('+', '\\+'),
                            request.headers.get('Authorization', [''])[0]):
                r = lib.webinterface.Http401Error('autoCSP').build_response()
                request.reply(r.build(request))
                raise EventPropagationStop()


@subscribe('request', enable_when_locked=False)
def handle_webinterface(request):
    path = request.get_path_components()
    if is_webinterface(path):
        response = lib.webinterface.call_view(request, '/' + '/'.join(path[1:]))
        request.reply(response.build(request))
        raise EventPropagationStop()
