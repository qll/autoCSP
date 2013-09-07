
""" Basic web interface. """
import lib.csp
import lib.utils

from lib.webinterface import make_response, path, Http400Error, Http404Error


style = '%(autocsp)s/static/style.css'


@path('/', csp={'style-src': [style]})
def index(req):
    """ Displays the index website. """
    query = ("SELECT document_uri FROM policy WHERE document_uri!='learn' GROUP"
             ' BY document_uri')
    uris = [uri[0] for uri in lib.utils.Globals()['db'].select(query)]
    return make_response('index.html', uris=uris)


@path('/policy', csp={'style-src': [style]})
def display_policy(req):
    """ Displays details of a policy. """
    params = req.get_query()
    if 'uri' not in params:
        raise Http400Error()
    uri = params['uri'][0]
    db = lib.utils.Globals()['db']
    rules = {}
    fullrules = []
    query = ('SELECT id, directive, uri, activated FROM policy WHERE '
             'document_uri=? ORDER BY directive, uri DESC')
    for id, directive, src, active in db.select(query, uri):
        if active:
            rules.setdefault(directive, []).append(src)
        fullrules.append([id, directive, src, active])
    if len(rules) == 0:
        raise Http404Error()
    return make_response('policy.html', document_uri=uri, rules=fullrules,
                                        policy=lib.csp.generate_policy(rules))
