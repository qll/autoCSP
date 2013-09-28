""" Basic web interface. """
import lib.csp
import lib.utils
import lib.webinterface

from settings import WEBINTERFACE_URI


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
@lib.webinterface.csrf
def display_policy(req, csrf_token):
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
    warnings = [{'id': i, 'text': t} for i, t in
                db.select('SELECT id, text FROM warnings WHERE document_uri=?',
                          uri)]
    return lib.webinterface.make_response('policy.html', document_uri=uri,
                                          rules=fullrules, warnings=warnings,
                                          policy=lib.csp.generate_policy(rules),
                                          csrf=csrf_token)


@lib.webinterface.path('/warning/delete')
@lib.webinterface.csrf
def delete_warning(req, csrf_token):
    """ Deletes a warning. """
    data = req.get_form_urlencoded()
    if 'id' not in data:
        raise lib.webinterface.Http400Error()
    db = lib.utils.Globals()['db']
    document_uri = db.fetch_one('SELECT document_uri FROM warnings WHERE id=?',
                                data['id'][0])[0]
    if not document_uri:
        raise lib.webinterface.Http404Error()
    db.execute('DELETE FROM warnings WHERE id=?', data['id'][0])
    return lib.webinterface.Redirect('/%s/policy?uri=%s' % (WEBINTERFACE_URI,
                                                            document_uri))


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/export')
def export(req):
    return lib.webinterface.make_response('export.html')
