""" Basic web interface. """
import urllib

import lib.csp
import lib.http
import lib.utils
import lib.webinterface

from settings import WEBINTERFACE_URI


style = '%(autocsp)s/static/style.css'


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/')
def index(req):
    """ Displays the index website. """
    db = lib.utils.Globals()['db']
    query = ('SELECT DISTINCT document_uri FROM policy WHERE document_uri!='
             "'learn' UNION SELECT DISTINCT inline.document_uri FROM inline, "
             'policy WHERE inline.document_uri!=policy.document_uri')
    uris = [uri[0] for uri in db.select(query)]
    c = db.fetch_one('SELECT COUNT(DISTINCT document_uri), COUNT(id) FROM '
                     "policy WHERE document_uri!='learn'")
    ci = db.fetch_one('SELECT COUNT(DISTINCT document_uri), COUNT(id) FROM '
                      'inline')
    overall_count = {'rules_uris': c[0], 'rules': c[1], 'inline_uris': ci[0],
                     'inline': ci[1]}
    return lib.webinterface.make_response('index.html', uris=uris,
                                          count=overall_count)


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/', mode='locked')
def locked_index(req):
    return lib.webinterface.make_response('locked_index.html')


@lib.webinterface.csp({'style-src': [style],
                       'script-src': ['%(autocsp)s/static/policy.js'],
                       'connect-src': ['%(autocsp)s/rule/active']})
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
    inline = [{'type': t, 'source': s} for t, s in
              db.select('SELECT type, source FROM inline WHERE document_uri=?',
                        uri)]
    if len(rules) == 0 and len(inline) == 0:
        raise lib.webinterface.Http404Error()
    warnings = [{'id': i, 'text': t} for i, t in
                db.select('SELECT id, text FROM warnings WHERE document_uri=?',
                          uri)]
    return lib.webinterface.make_response('policy.html', document_uri=uri,
                                          rules=fullrules, warnings=warnings,
                                          policy=lib.csp.generate_policy(rules),
                                          csrf=csrf_token, inline=inline)


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
                                     urllib.quote(document_uri)))


@lib.webinterface.path('/rule/active')
@lib.webinterface.csrf
def set_status(req, csrf_token):
    data = req.get_form_urlencoded()
    if 'id' not in data or 'active' not in data:
        raise lib.webinterface.Http400Error()
    db = lib.utils.Globals()['db']
    active = data['active'][0]
    id = data['id'][0]
    db.execute('UPDATE policy SET activated=? WHERE id=?', (active, id))
    return lib.http.Response(content=csrf_token)


@lib.webinterface.csp({'style-src': [style]})
@lib.webinterface.path('/export')
def export(req):
    return lib.webinterface.make_response('export.html')
