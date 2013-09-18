""" Basic web interface. """
import lib.csp
import lib.utils
import lib.webinterface


style = '%(autocsp)s/static/style.css'


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/')
def index(req):
    """ Displays the index website. """
    query = ("SELECT document_uri FROM policy WHERE document_uri!='learn' GROUP"
             ' BY document_uri')
    uris = [uri[0] for uri in lib.utils.Globals()['db'].select(query)]
    return lib.webinterface.make_response('index.html', uris=uris)


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/', mode='locked')
def locked_index(req):
    return lib.webinterface.make_response('locked_index.html')


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/policy')
def display_policy(req):
    """ Displays details of a policy. """
    params = req.get_query()
    if 'uri' not in params:
        raise lib.webinterface.Http400Error()
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
        raise lib.webinterface.Http404Error()
    warnings = [w[0] for w in db.select('SELECT text FROM warnings WHERE '
                                        'document_uri = ?', uri)]
    return lib.webinterface.make_response('policy.html', document_uri=uri,
                                          rules=fullrules, warnings=warnings,
                                          policy=lib.csp.generate_policy(rules))


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/export')
def export(req):
    return lib.webinterface.make_response('export.html')
