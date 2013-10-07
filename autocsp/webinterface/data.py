""" Data-retrieving views. """
import hashlib
import json
import os
import re
import urllib

import lib.csp
import lib.utils
import lib.http
import lib.webinterface
import webinterface.static

from settings import ORIGIN, PATHS, DEBUG, LOCKED_MODE, WEBINTERFACE_URI


def strip_query(uri, document_uri, db):
    """ Checks if uri has a query part and strips it. Adds a warning to the
        database to inform the user that this could pose a security risk. """
    has_query = re.match('(^.+)\?(.*$)', uri)
    if has_query:
        uri = has_query.group(1)
        if has_query.group(2) and not document_uri == 'learn':
            warning = ('%s may be a dynamic script due to observed query '
                       'parameters. This can subvert the CSP if inputs are not '
                       'sanitized properly.') % uri
            db.execute('INSERT OR IGNORE INTO warnings VALUES (NULL, ?, ?)',
                       (document_uri, warning))
    return uri


def parse_query(query):
    """ Parses URL-encoded parameters. """
    data = {}
    for component in query.split('&'):
        if '=' in component:
            p, v = component.split('=', 1)
            data[urllib.unquote(p)] = urllib.unquote(v)
    return data


@lib.webinterface.path('/_/policy')
def refine_policy(req):
    """ Refines the policy obtained with the Report-Only header. """
    data = parse_query(req.content)
    if 'data' not in data or 'uri' not in data or 'id' not in data:
        raise lib.webinterface.Http400Error('Incomplete policy report.')
    data['data'] = json.loads(data['data'])
    db = lib.utils.Globals()['db']
    for directive, uris in data['data'].items():
        if directive in lib.csp.directives:
            for uri in uris:
                if not db.count('policy WHERE document_uri = ? AND directive = '
                                '? AND uri = ?', (data['uri'], directive, uri)):
                    ext_origin = re.match('(^https?://[^/]+)', uri,
                                          re.I).group(1)
                    uri = strip_query(uri, data['uri'], db)
                    # set unspecific rule to not activated ... there has to be one
                    db.execute('UPDATE policy SET activated = 0 WHERE '
                               'document_uri = ? AND directive = ? AND uri = ?',
                               (data['uri'], directive, ext_origin))
                    db.execute('INSERT INTO policy VALUES (NULL, ?, ?, ?, ?, 1'
                               ')', (data['uri'], directive, uri, data['id']))


@lib.webinterface.path('/_/report')
def save_report(req):
    """ Saves a CSP violation report to the policy database table. """
    data = json.loads(req.content)
    params = req.get_query()
    if 'id' not in params:
        raise lib.webinterface.Http400Error('Violation report lacked an id.')
    if 'csp-report' not in data:
        raise lib.webinterface.Http400Error('Incomplete violation report.')
    report = data['csp-report']
    request_id = params['id'][0]
    if ('violated-directive' not in report or 'blocked-uri' not in report
        or report['blocked-uri'] == '' or 'document-uri' not in report or
        ' ' not in report['violated-directive']):
        # ignore incomplete or broken reports
        return
    directive = report['violated-directive'].split(' ')[0]
    blocked_uri = report['blocked-uri']
    if directive not in lib.csp.directives:
        # ignore broken directives
        return
    origin, document_uri = re.match('(^https?://[^/]+)(.*)$',
                                    report['document-uri'], re.I).groups()
    activated = 1
    db = lib.utils.Globals()['db']
    if blocked_uri.startswith(origin):
        # cut same origin URIs so that they start with /
        blocked_uri = blocked_uri[len(origin):]
    else:
        id = db.fetch_one('SELECT id FROM policy WHERE document_uri=? AND '
                          'directive=? AND uri=? AND activated=0 AND '
                          'request_id!=?', (document_uri, directive,
                                            blocked_uri, request_id))
        if id:
            id = id[0]
            # refined policy is missing something - disable all refinements :(
            db.execute('UPDATE policy SET activated=1, request_id=? WHERE id=?',
                       (request_id, id))
            db.execute('UPDATE policy SET activated=0 WHERE document_uri=? AND'
                       ' directive=? AND uri LIKE ?',
                       (document_uri, directive, report['blocked-uri'] + '/%'))
            return
        # check for unlikely race condition: specific URIs exist -> activated=0
        rules = db.count('policy WHERE activated=1 AND request_id=? AND '
                         'document_uri = ? and directive = ? and uri LIKE ?',
                         (request_id, document_uri, directive,
                          blocked_uri + '/%'))
        activated = 0 if rules else 1
    if blocked_uri.startswith('/%s/_' % WEBINTERFACE_URI):
        # backend URIs whitelisted for every ressource
        document_uri = 'learn'
    blocked_uri = strip_query(blocked_uri, document_uri, db)
    db.execute('INSERT OR IGNORE INTO policy VALUES (NULL, ?, ?, ?, ?, ?)',
               (document_uri, directive, blocked_uri, request_id, activated))


def wrap_static(content, ext):
    """ Wraps static content in a Response object w/ correct MIME-type. """
    r = lib.http.Response(content=content)
    r.set_header('Content-Type', '%s; charset=UTF-8' %
                                 webinterface.static.mime_types[ext])
    return r


def serve_scripts(scripts):
    """ Combines one or more script files into one and embeds them in the
        small autoCSP JavaScript framework. """
    debug = DEBUG and not LOCKED_MODE
    views_path = os.path.expanduser(PATHS['VIEWS'])
    with open(views_path + 'static/sha256.js', 'r') as f:
        sha256js = f.read()
    template = lib.webinterface.render_template('framework.js', debug=debug,
                                                scripts=scripts,
                                                sha256js=sha256js)
    return wrap_static(template, '.js')


def check_referer(headers, document_uri):
    """ Checks if the Referer differs from the document_uri. The Referer Header
        is just a bad way to do this so this is mereley an additional
        hurdle. """
    if 'Referer' not in headers:
        return
    referer = headers['Referer'][0]
    origin = lib.utils.assemble_origin(ORIGIN)
    if referer != origin + document_uri:
        raise lib.webinterface.Http403Error()


@lib.webinterface.path('/_/inline(/.*).js', mode='locked')
def serve_inlinejs(req, document_uri):
    """ Serves the inline.js script handling inline styles in locked mode. """
    check_referer(req.headers, document_uri)
    db = lib.utils.Globals()['db']
    events = [{'source': s.split(',', 2)[2], 'hash': h} for s, h in
              db.select('SELECT source, hash FROM inline WHERE document_uri=? '
                        "AND type='js-event'", document_uri)]
    links = [{'source': s.split(',', 1)[1], 'hash': h} for s, h in
              db.select('SELECT source, hash FROM inline WHERE document_uri=? '
                        "AND type='js-link'", document_uri)]
    sources = [{'source': s, 'hash': h} for s, h in
               db.select('SELECT source, hash FROM inline WHERE document_uri=? '
                         "AND type='js'", document_uri)]
    inlinejs = lib.webinterface.render_template('inline.js', events=events,
                                                             sources=sources,
                                                             links=links)
    return serve_scripts((inlinejs,))


@lib.webinterface.path('/_/inline(/.*).css', mode='locked')
def serve_inlinecss(req, document_uri):
    """ Serves the inline.css stylesheet containing all inline styles in locked
        mode. """
    check_referer(req.headers, document_uri)
    db = lib.utils.Globals()['db']
    styles = [s[0] for s in
              db.select('SELECT source FROM inline WHERE document_uri = ? AND '
                        "type = 'css'", document_uri)]
    attributes = []
    query = ('SELECT source, hash FROM inline WHERE document_uri=? AND type='
             "'css-attr'")
    for s, h in db.select(query, document_uri):
        # if no ; at the end set one (for adding !important)
        if re.search(r'[^\s;]\s*$', s):
            s += ';'
        s = s.replace(';', ' !important;')
        attributes.append({'source': s, 'hash': h})
    template = lib.webinterface.render_template('inline.css', styles=styles,
                                                attributes=attributes)
    return wrap_static(template, '.css')


@lib.webinterface.path('/_/learning.js')
def serve_learningjs(req):
    """ Serves combination of policy.js and externalize.js. """
    db = lib.utils.Globals()['db']
    document_uri = req.get_query()['document_uri'][0]
    known_hashes = ["'%s'" % h[0] for h in
                    db.select('SELECT hash FROM inline WHERE document_uri = ?',
                              document_uri)]
    origin = lib.utils.assemble_origin(ORIGIN)
    report_uri = '%s/%s/_/policy' % (origin, WEBINTERFACE_URI)
    ext_uri = '%s/%s/_/externalize' % (origin, WEBINTERFACE_URI)
    scripts = (lib.webinterface.render_template('policy.js',
                                                report_uri=report_uri),
               lib.webinterface.render_template('externalize.js',
                                                externalizer_uri=ext_uri,
                                                known_hashes=known_hashes))
    return serve_scripts(scripts)


@lib.webinterface.path('/_/externalize')
def save_inline(req):
    """ Saves inline scripts and styles to the database for externalization. """
    data = parse_query(req.content)
    if 'data' not in data or 'uri' not in data or 'id' not in data:
        raise lib.webinterface.Http400Error('Incomplete externalize request.')
    db = lib.utils.Globals()['db']
    inline = json.loads(data['data'])
    for type, sources in inline.items():
        if type not in ('css', 'css-attr', 'js', 'js-event', 'js-link'):
            continue
        for source in sources:
            hash = hashlib.sha256(source).hexdigest()
            db.execute('INSERT OR IGNORE INTO inline VALUES (NULL, ?, ?, ?, ?, '
                       '?)', (data['uri'], type, source, hash, data['id']))
