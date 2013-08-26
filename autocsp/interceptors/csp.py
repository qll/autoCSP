import re

import lib.globals

from lib.events import subscribe
from settings import WEBINTERFACE_URI


policy_rules = ('script-src', 'img-src')


@subscribe('db_init')
def create_tables(db):
    db.execute('CREATE TABLE policy (id INTEGER PRIMARY KEY AUTOINCREMENT, '
               'internal_uri TEXT, directive TEXT, uri TEXT, '
               'UNIQUE (internal_uri, directive, uri))')


@subscribe('response')
def clear_csp_header(request):
    """ Strips existing CSP headers. """
    for field in ('Content-Security-Policy', 'X-WebKit-CSP',
                  'X-Content-Security-Policy', 'X-WebKit-CSP-Report-Only',
                  'X-Content-Security-Policy-Report-Only',
                  'Content-Security-Policy-Report-Only'):
        if field in request.headers:
            del request.headers[field]


# policy generation via violation reports is bad (see thesis)
#@subscribe('response')
def add_report_csp_header(resp):
    """ Adds a Report-Only CSP header. """
    policy = ["default-src 'none'; script-src 'none'; style-src 'none'; "
              "img-src 'none'; connect-src 'none'; font-src 'none'; "
              "object-src 'none'; media-src 'none'; frame-src 'none'; "
              "report-uri /_autoCSP/_/report;"]
    resp.headers['Content-Security-Policy-Report-Only'] = policy


@subscribe('response', mode='learning')
def inject_script(resp):
    """ Injects a script into every served HTML page (policy generation). """
    if 'Content-Type' in resp.headers:
        if re.match('\s*text/x?html*.', ''.join(resp.headers['Content-Type'])):
            inj = ('<script src="/%s/_/policy.js"></script>'
                   % WEBINTERFACE_URI)
            # inject after <head>
            if '<head' in resp.content:
                resp.content = re.sub('(<head[^>]*>)',
                                      lambda m: m.group(1) + inj,
                                      resp.content, 1)
            # inject after <title>
            elif '<title' in resp.content:
                resp.content = re.sub('(<title[^>]*>)',
                                      lambda m: inj + m.group(1),
                                      resp.content, 1)
            # if all fails just prepend to content
            if inj not in resp.content:
                resp.content = inj + resp.content


@subscribe('response', mode='locked')
def inject_csp(resp):
    """ Injects a Content Security Policy to protect the site. """
    db = lib.globals.Globals()['db']
    rules = {}
    for directive, src in db.select(('SELECT directive, uri FROM policy WHERE '
                                     'internal_uri = ?'), (resp.request.path,)):
        rules.setdefault(directive, []).append(src)
    policy = ['%s %s' % (d, ' '.join(rules.setdefault(d, ["'none'"])))
              for d in policy_rules]
    # TODO(qll): FireFox does not know file path specific CSP directives, yet...
    resp.headers['Content-Security-Policy'] = ['; '.join(policy)]
