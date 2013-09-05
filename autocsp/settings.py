
# when locked mode is disabled the proxy will build up a policy which can be
# enforced when locked mode is enabled again
LOCKED_MODE = False

# (protocol, host, port) which will be reverse proxied
REVERSE_PROXY = ('http', 'localhost', 8000)

# debug mode enables console logs for developers (auto-disabled in locked mode)
DEBUG = True

# URI path prefix for internal autoCSP URLs (webinterface)
WEBINTERFACE_URI = '_autoCSP'

# HTTP Basic Authentication for the web interface. None or ('user', 'pass').
WEBINTERFACE_AUTH = None

# enabled interceptors (order matters)
INTERCEPTORS = ('webinterface', 'caching', 'csp')

PATHS = {
    # path to sqlite3 database (does not have to exist)
    'DATABASE': 'proxy.sqlite',
    # path to all interceptor functions (w/ trailing slash)
    'INTERCEPTORS': 'interceptors/',
    # path to all View functions (w/ trailing slash)
    'VIEWS': 'webinterface/',
    # path to the CA certificate
    'CACERT': '~/.mitmproxy/mitmproxy-ca.pem',
}
