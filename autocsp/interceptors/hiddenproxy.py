from lib.events import subscribe
from settings import REVERSE_PROXY


@subscribe('request')
def change_hostname(req):
    host = REVERSE_PROXY[1] + (':%d' % REVERSE_PROXY[2]
                               if REVERSE_PROXY[2] != 80 else '')
    req.headers['host'] = [host]
