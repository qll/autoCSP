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
    if '&' in req.content:
        data = {}
        for component in req.content.split('&'):
            if '=' in component:
                p, v = component.split('=', 1)
                data[urllib.unquote(p)] = urllib.unquote(v)
        if {'sources', 'uri'} > set(data.keys()):
            raise lib.webinterface.Http400Error()
        data['sources'] = json.loads(data['sources'])
        db = lib.globals.Globals()['db']
        for rule in lib.csp.directives:
            if rule in data['sources'] and isinstance(data['sources'][rule],
                                                      list):
                for insert in data['sources'][rule]:
                    # XXX: possible performance problem
                    db.execute('INSERT INTO policy VALUES (NULL, ?, ?, ?)',
                               (data['uri'], rule, insert))
    return ''


@lib.webinterface.path('/_/report')
def save_report(req):
    """ Saves a CSP violation report to the policy database table. """
    data = json.loads(req.content)
    params = req.get_query()
    if 'id' not in params:
        raise Exception('Violation report lacked an id.')
    if 'csp-report' not in data:
        raise Exception('csp-report not found in JSON data.')
    report = data['csp-report']
    if ('effective-directive' not in report or 'blocked-uri' not in report
        or report['blocked-uri'] == '' or 'document-uri' not in report or
        report['effective-directive'] not in lib.csp.directives):
        return
    document_uri = re.sub('^https?://[^/]+', '', report['document-uri'], 1,
                          re.I)
    db = lib.globals.Globals()['db']
    db.execute(('INSERT OR REPLACE INTO policy VALUES (NULL, :docuri, :dir, '
                ':uri, :reqid, (SELECT count(count) FROM policy WHERE '
                'request_id = :reqid) + 1)'),  # counts up to 2
               {'docuri': document_uri, 'dir': report['effective-directive'],
                'uri': report['blocked-uri'], 'reqid': params['id'][0]})
    return
