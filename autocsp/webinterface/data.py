""" Data-retrieving views. """
import json
import re
import urllib

import lib.csp
import lib.globals
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
    db = lib.globals.Globals()['db']
    for directive, uris in data['sources'].items():
        if directive in lib.csp.directives:
            for uri in uris:
                if not db.count('policy WHERE document_uri = ? AND directive = '
                                '? AND uri = ?', (data['uri'], directive, uri)):
                    ext_origin = re.match('(^https?://[^/]+)', uri,
                                          re.I).group(1)
                    # set unspecific rule to not activated
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
    if ('violated-directive' not in report or 'blocked-uri' not in report
        or report['blocked-uri'] == '' or 'document-uri' not in report or
        ' ' not in report['violated-directive']):
        # ignore incomplete or broken reports
        return
    directive = report['violated-directive'].split(' ')[0]
    if directive not in lib.csp.directives:
        # ignore broken directives
        return
    origin, document_uri = re.match('(^https?://[^/]+)(.*)$',
                                    report['document-uri'], re.I).groups()
    db = lib.globals.Globals()['db']
    """ XXX
    if (not report['blocked-uri'].startswith(origin) and
        db.count('policy WHERE document_uri = ? AND directive = ? AND uri '
                 '= ? AND activated = 0 AND report_id != ?'), ()):

        return
    """
    if report['blocked-uri'].startswith('%s/%s/_' % (origin, WEBINTERFACE_URI)):
        # internal data URIs to learn whitelist
        document_uri = 'learn'
    db.execute('INSERT OR IGNORE INTO policy VALUES (NULL, ?, ?, ?, ?, 1)',
               (document_uri, directive, report['blocked-uri'],
                params['id'][0]))
