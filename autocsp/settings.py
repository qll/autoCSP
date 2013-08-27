
# if locked mode is enabled, the CSP policy will be enforced, else the proxy
# learns about the site first (while browsing it)
LOCKED_MODE = True

# (schema, host, port) which will be reverse proxied
REVERSE_PROXY = ('http', 'localhost', 8000)

# URI path prefix for internal autoCSP URLs (webinterface)
WEBINTERFACE_URI = '_autoCSP'

# HTTP Basic Authentication for the web interface. None or ('user', 'pass').
WEBINTERFACE_AUTH = None

# enabled interceptors (order matters)
INTERCEPTORS = (
    'webinterface',
    'csp',
)

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
