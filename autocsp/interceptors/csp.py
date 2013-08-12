from lib.events import subscribe


@subscribe('response')
def clear_csp_header(request):
    """ Strip existing CSP headers. """
    for field in ('Content-Security-Policy', 'X-WebKit-CSP',
                  'X-Content-Security-Policy', 'X-WebKit-CSP-Report-Only',
                  'X-Content-Security-Policy-Report-Only',
                  'Content-Security-Policy-Report-Only'):
        if field in request.headers:
            del request.headers[field]


@subscribe('response')
def add_report_csp_header(req):
    """ Adds a Report-Only CSP header. """
    policy = ["default-src 'none'; script-src 'none'; style-src 'none'; "
              "img-src 'none'; connect-src 'none'; font-src 'none'; "
              "object-src 'none'; media-src 'none'; frame-src 'none'; "
              "report-uri /_autoCSP/_/report;"]
    req.headers['Content-Security-Policy-Report-Only'] = policy
