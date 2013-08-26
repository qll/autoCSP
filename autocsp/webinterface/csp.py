import lib.http
import webinterface.static

from lib.webinterface import path, render_template
from settings import WEBINTERFACE_URI


@path('/_/policy.js')
def serve_policy(req):
    ''' Serves the policy.js script. '''
    template = render_template('policy.js', report_uri='/%s/_/policy'
                                                       % WEBINTERFACE_URI)
    r = lib.http.Response(content=template)
    r.set_header('Content-Type', '%s; charset=UTF-8' %
                                 webinterface.static.mime_types['.js'])
    return r


@path('/_/policy')
def report_policy(req):
    ''' CSP policy.js sink. Writes all gathered information to database. '''
    print(req.content)
    return ''
