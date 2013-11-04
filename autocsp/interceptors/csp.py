import random
import re
import string
import urllib

import lib.csp
import lib.utils

from lib.events import subscribe
from settings import ORIGIN, REWRITE_INLINE, WEBINTERFACE_URI


@subscribe('db_init')
def create_tables(db):
    db.execute('CREATE TABLE policy (id INTEGER PRIMARY KEY AUTOINCREMENT, '
               'document_uri TEXT, directive TEXT, uri TEXT, request_id TEXT, '
               'activated INTEGER, UNIQUE (document_uri, directive, uri))')
    db.execute('CREATE TABLE warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, '
               'document_uri TEXT, text TEXT, UNIQUE (document_uri, text))')
    db.execute('CREATE TABLE violations (id INTEGER PRIMARY KEY AUTOINCREMENT, '
               'report TEXT, UNIQUE (report))')
    db.execute('CREATE TABLE inline (id INTEGER PRIMARY KEY AUTOINCREMENT, '
               'document_uri TEXT, type TEXT, source TEXT, hash TEXT, '
               'request_id TEXT, UNIQUE (document_uri, type, hash))')


@subscribe('response')
def clear_csp_headers(request):
    """ Strips existing CSP headers. """
    for field in ('Content-Security-Policy', 'X-WebKit-CSP',
                  'X-Content-Security-Policy', 'X-WebKit-CSP-Report-Only',
                  'X-Content-Security-Policy-Report-Only',
                  'Content-Security-Policy-Report-Only'):
        if field in request.headers:
            del request.headers[field]


def generate_id(length):
    """ Generates an id for the identification of violation reports. """
    abc = string.digits + string.letters
    return ''.join(random.choice(abc) for _ in range(length))


def add_report_header(resp, id):
    """ Adds a Report-Only CSP header (policy generation). """
    db = lib.utils.Globals()['db']
    rules = {}
    for directive, src in db.select('SELECT directive, uri FROM policy WHERE '
                                    'activated=1 AND document_uri=? OR '
                                    "document_uri='learn'", resp.request.path):
        rules.setdefault(directive, []).append(src)
    policy = lib.csp.generate_policy(rules)
    policy += '; report-uri /%s/_/report?id=%s' % (WEBINTERFACE_URI, id)
    resp.headers['Content-Security-Policy-Report-Only'] = [policy]


def inject_markup(resp, markup):
    """ Try to inject markup in HTTP response. """
    # inject after <head>
    if '<head' in resp.content:
        resp.content = re.sub('(<head[^>]*>)',
                              lambda m: m.group(1) + markup,
                              resp.content, 1)
    # inject after <title>
    elif '<title' in resp.content:
        resp.content = re.sub('(<title[^>]*>)',
                              lambda m: markup + m.group(1),
                              resp.content, 1)
    # if all fails just prepend to content
    if markup not in resp.content:
        resp.content = markup + resp.content


def inject_script(resp, id):
    """ Injects a script into every served HTML page (policy generation). """
    if 'Content-Type' in resp.headers:
        if re.search('^\s*(text\/html|application\/xhtml\+xml).*$',
                     ''.join(resp.headers['Content-Type'])):
            doc_uri = urllib.quote(resp.request.path)
            inj = ('<script src="/%s/_/learning.js?document_uri=%s" '
                   'data-id="%s"></script>' % (WEBINTERFACE_URI, doc_uri, id))
            inject_markup(resp, inj)


@subscribe('response', mode='learning')
def add_csp_reports(resp):
    """ Adds the CSP Report-Only header and policy.js for policy generation. """
    # nonce for request identification (request_id)
    id = generate_id(32)
    add_report_header(resp, id)
    inject_script(resp, id)


@subscribe('response', mode='locked')
def inject_csp(resp):
    """ Injects a CSP to protect the webapp (policy enforcement). """
    document_uri = resp.request.path
    quoted_docuri = urllib.quote(resp.request.path)
    db = lib.utils.Globals()['db']
    rules = {}
    for directive, src in db.select('SELECT directive, uri FROM policy WHERE '
                                    'document_uri=? AND activated=1',
                                    document_uri):
        rules.setdefault(directive, []).append(src)
    if REWRITE_INLINE:
        css = db.count("inline WHERE document_uri=? AND type LIKE 'css%'",
                       document_uri)
        origin = lib.utils.assemble_origin(ORIGIN)
        data_uri = '%s/%s/_/' % (origin, WEBINTERFACE_URI)
        if css:
            css_uri = '%s%sautoCSPinline.css' % (origin, resp.request.path)
            rules.setdefault('style-src', []).append(css_uri)
            css_markup = '<link rel="stylesheet" href="%s" />' % css_uri
            inject_markup(resp, css_markup)
        js = db.count("inline WHERE document_uri=? AND type LIKE 'js%'",
                      document_uri)
        if css or js:
            js_uri = '%sinline%s.js' % (data_uri, quoted_docuri)
            rules.setdefault('script-src', []).append(js_uri)
            js_markup = '<script src="%s"></script>' % js_uri
            inject_markup(resp, js_markup)
        if js:
            extjs_uri = '%sexternalized%s.js' % (data_uri, quoted_docuri)
            rules.setdefault('script-src', []).append(extjs_uri)
    if not rules and '?' in document_uri:
        resp.request.path = document_uri.split('?', 1)[0]
        inject_csp(resp)
    else:
        policy = "default-src 'none'; " + lib.csp.generate_policy(rules)
        resp.headers['Content-Security-Policy'] = [policy]
