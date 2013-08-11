from libmproxy import flow
from netlib.odict import ODictCaseless


status_codes = {
    200: 'OK',
    401: 'Unauthorized',
    404: 'Not Found',
}


# HTTP/1.1 and HTTP/1.0
http_versions = ((1, 1), (1, 0))


class InvalidStatusCodeError(Exception):
    pass


class InvalidHttpVersionError(Exception):
    pass


class HttpMessage(object):
    pass


class Response(HttpMessage):
    def __init__(self, content='', status_code=200, http_version=(1, 1)):
        if status_code not in status_codes:
            raise InvalidStatusCodeError('Unknown HTTP status code (%s).'
                                         % status_code)
        if http_version not in http_versions:
            raise InvalidHttpVersionError('Unknown HTTP version %s.'
                                          % http_version)
        self.content = content
        self.status_code = status_code
        self.http_version = http_version
        self.headers = {'Content-Type': 'text/html; charset=UTF-8',
                        'X-Frame-Options': 'DENY',  # prevent framing
                        'X-XSS-Protection': '1; mode=block'}  # XSS blacklist
        self.cert = None

    def set_header(self, field, value):
        self.headers[field] = value

    def build(self, request):
        """ Builds a libmproxy flow.Response. """
        headers = ODictCaseless([(k, v) for k, v in self.headers.items()])
        return flow.Response(request, self.http_version, self.status_code,
                             status_codes[self.status_code], headers,
                             self.content, self.cert)
