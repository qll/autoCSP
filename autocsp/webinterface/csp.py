import json
import urllib

import lib.csp
import lib.globals
import lib.http
import webinterface.static

from lib.webinterface import path, render_template, Http400Error
from settings import DEBUG, WEBINTERFACE_URI


@path('/_/policy.js')
def serve_policy(req):
    ''' Serves the policy.js script. '''
    report_uri = '/%s/_/policy' % WEBINTERFACE_URI
    template = render_template('policy.js', report_uri=report_uri, debug=DEBUG)
    r = lib.http.Response(content=template)
    r.set_header('Content-Type', '%s; charset=UTF-8' %
                                 webinterface.static.mime_types['.js'])
    return r


@path('/_/policy')
def report_policy(req):
    ''' CSP policy.js sink. Writes all gathered information to database. '''
    if '&' in req.content:
        data = {}
        for component in req.content.split('&'):
            if '=' in component:
                p, v = component.split('=', 1)
                data[urllib.unquote(p)] = urllib.unquote(v)
        if {'sources', 'uri'} > set(data.keys()):
            raise Http400Error()
        data['sources'] = json.loads(data['sources'])
        db = lib.globals.Globals()['db']
        for rule in lib.csp.rules:
            if rule in data['sources'] and isinstance(data['sources'][rule],
                                                      list):
                for insert in data['sources'][rule]:
                    # XXX: possible performance problem
                    db.execute('INSERT INTO policy VALUES (NULL, ?, ?, ?)',
                               (data['uri'], rule, insert))
    return ''
