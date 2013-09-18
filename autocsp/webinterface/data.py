""" Data-retrieving views. """
import json
import re
import urllib

import lib.csp
import lib.utils
import lib.http
import lib.webinterface
import webinterface.static

from settings import DEBUG, WEBINTERFACE_URI


@lib.webinterface.path('/_/policy.js')
def serve_policy(req):
    """ Serves the policy.js script. """
    report_uri = '/%s/_/policy' % WEBINTERFACE_URI
    template = lib.webinterface.render_template('policy.js',
                                                report_uri=report_uri,
                                                debug=DEBUG)
    r = lib.http.Response(content=template)
    r.set_header('Content-Type', '%s; charset=UTF-8' %
                                 webinterface.static.mime_types['.js'])
    return r


def strip_query(uri, document_uri, db):
    """ Checks if uri has a query part and strips it. Adds a warning to the
        database to inform the user that this could pose a security risk. """
    has_query = re.match('(^.+)\?(.*$)', uri)
    if has_query:
        uri = has_query.group(1)
        if has_query.group(2):
            warning = ('%s may be a dynamic script due to observed query '
                       'parameters. This can subvert the CSP if inputs are not '
                       'sanitized properly.') % uri
            db.execute('INSERT OR IGNORE INTO warnings VALUES (NULL, ?, ?)',
                       (document_uri, warning))
    return uri


@lib.webinterface.path('/_/policy')
def refine_policy(req):
    """ Refines the policy obtained with the Report-Only header. """
    if '&' not in req.content:
        return
    data = {}
    for component in req.content.split('&'):
        if '=' in component:
            p, v = component.split('=', 1)
            data[urllib.unquote(p)] = urllib.unquote(v)
    if 'sources' not in data or 'uri' not in data or 'id' not in data:
        raise lib.webinterface.Http400Error('Incomplete policy report.')
    data['sources'] = json.loads(data['sources'])
    db = lib.utils.Globals()['db']
    for directive, uris in data['sources'].items():
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
    blocked_uri = strip_query(blocked_uri, document_uri, db)
    if blocked_uri.startswith('/%s/_' % WEBINTERFACE_URI):
        # backend URIs whitelisted for every ressource
        document_uri = 'learn'
    db.execute('INSERT OR IGNORE INTO policy VALUES (NULL, ?, ?, ?, ?, ?)',
               (document_uri, directive, blocked_uri, request_id, activated))
