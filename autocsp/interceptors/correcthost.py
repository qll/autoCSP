import lib.webinterface

from lib.events import subscribe, EventPropagationStop
from settings import ORIGIN


@subscribe('request')
def check_host(req):
    host = ORIGIN[1] + ':%d' % ORIGIN[2] if ORIGIN != 80 else ''
    if 'host' not in req.headers or req.headers['host'][0] != host:
        req.reply(lib.webinterface.Http400Error().build_response().build(req))
        raise EventPropagationStop()
