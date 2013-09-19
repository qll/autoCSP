import random
import re
import string

import lib.csp
import lib.utils

from lib.events import subscribe
from settings import WEBINTERFACE_URI


@subscribe('db_init')
def create_tables(db):
    db.execute('CREATE TABLE policy (id INTEGER PRIMARY KEY AUTOINCREMENT, '
               'document_uri TEXT, directive TEXT, uri TEXT, request_id TEXT, '
               'activated INTEGER, UNIQUE (document_uri, directive, uri))')
    db.execute('CREATE TABLE warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, '
               'document_uri TEXT, text TEXT, UNIQUE (document_uri, text))')
    db.execute('CREATE TABLE violations (id INTEGER PRIMARY KEY AUTOINCREMENT,'
               'report TEXT, UNIQUE report)')


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


def inject_script(resp, id):
    """ Injects a script into every served HTML page (policy generation). """
    if 'Content-Type' in resp.headers:
        if re.match('\s*text/x?html*.', ''.join(resp.headers['Content-Type'])):
            inj = ('<script src="/%s/_/policy.js" data-id="%s"></script>'
                   % (WEBINTERFACE_URI, id))
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
    db = lib.utils.Globals()['db']
    rules = {}
    for directive, src in db.select('SELECT directive, uri FROM policy WHERE '
                                    'document_uri=? AND activated=1',
                                    resp.request.path):
        rules.setdefault(directive, []).append(src)
    policy = "default-src 'none'; " + lib.csp.generate_policy(rules)
    resp.headers['Content-Security-Policy'] = [policy]
