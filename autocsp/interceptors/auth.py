import base64
import logging
import re

import lib.webinterface

from lib.events import subscribe, EventPropagationStop
from settings import AUTH, LOCKED_MODE, LOCKED_WEBINTERFACE


logger = logging.getLogger(__name__)


mode = ''
if ((AUTH['learning'] and AUTH['locked']) or
    (AUTH['webinterface'] and LOCKED_WEBINTERFACE)):
    mode = '*'
elif AUTH['learning']:
    mode = 'learning'
elif AUTH['locked']:
    mode = 'locked'


def check_credentials(credentials, headers):
    auth = base64.standard_b64encode('%s:%s' % (credentials[0],
                                                credentials[1]))
    return (True if re.match('^\s*Basic %s\s*$' % auth.replace('+', '\\+'),
                             headers.get('Authorization', [''])[0])
                 else False)


if mode:
    logger.debug('HTTP Basic Auth is enabled.')

    @subscribe('request', mode=mode)
    def add_auth(req):
        """ Adds HTTP Basic Authentication to the web application. """
        credentials = list()
        path = req.get_path_components()
        if (lib.webinterface.is_webinterface(path) and AUTH['webinterface']
            and not lib.webinterface.is_datasink(path)):
            credentials = AUTH['webinterface']
        elif LOCKED_MODE and AUTH['locked']:
            credentials = AUTH['locked']
        elif not LOCKED_MODE and AUTH['learning']:
            credentials = AUTH['learning']
        if credentials:
            if not check_credentials(credentials, req.headers):
                r = lib.webinterface.Http401Error('autoCSP').build_response()
                req.reply(r.build(req))
                raise EventPropagationStop()
