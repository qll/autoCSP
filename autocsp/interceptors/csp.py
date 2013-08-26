import re

from lib.events import subscribe
from settings import WEBINTERFACE_URI


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


@subscribe('response')
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
