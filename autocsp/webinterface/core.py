import lib.csp
import lib.globals

from lib.webinterface import make_response, path


@path('/')
def index(req):
    query = 'SELECT internal_uri FROM policy GROUP BY internal_uri'
    uris = [uri[0] for uri in lib.globals.Globals()['db'].select(query)]
    return make_response('index.html', uris=uris)
