from lib.events import subscribe


@subscribe('response')
def clear_csp_header(request):
    """ Clears existing CSP headers. """
    for field in ('Content-Security-Policy', 'X-WebKit-CSP',
                  'X-Content-Security-Policy'):
        if field in request.headers:
            del request.headers[field]


@subscribe('response')
def add_report_csp_header(req):
    """ Adds a report-only CSP header. """
    req.headers['Content-Security-Policy'] = ["default-src 'self'; ...; "
                                              "report-uri /_autoCSP/_/report;"]
