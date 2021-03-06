import re

import lib.http
import lib.webinterface

from lib.events import subscribe, EventPropagationStop
from settings import AUTH, LOCKED_MODE, LOCKED_WEBINTERFACE


@subscribe('response')
def ignore_webinterface(resp):
    path = resp.request.get_path_components()
    if lib.webinterface.is_webinterface(path):
        if (not lib.webinterface.is_datasink(path) and
            (LOCKED_MODE and (not LOCKED_WEBINTERFACE or
                              not AUTH['webinterface']))):
            return
        raise EventPropagationStop()


@subscribe('request')
def handle_webinterface(req):
    path = req.get_path_components()
    if lib.webinterface.is_webinterface(path):
        if (not lib.webinterface.is_datasink(path) and
            (LOCKED_MODE and (not LOCKED_WEBINTERFACE or
                              not AUTH['webinterface']))):
            return
        response = lib.webinterface.call_view(req, '/' + '/'.join(path[1:]))
        req.reply(response.build(req))
        raise EventPropagationStop()


@subscribe('request', mode='locked')
def handle_inlinecss(req):
    match = re.search(r'^(.*)autoCSPinline.css$', req.path)
    if match:
        response = lib.webinterface.call_view(req, '/_/inline%s.css' %
                                                   match.group(1))
        if response.content.strip():
            req.reply(response.build(req))
            raise EventPropagationStop()
