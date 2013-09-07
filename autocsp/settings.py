
# when locked mode is disabled the proxy will build up a policy which can be
# enforced when locked mode is enabled again
LOCKED_MODE = False

# (protocol, host, port) of the server reverse proxied
REVERSE_PROXY = ('http', 'localhost', 8000)

# the web origin this reverse proxy represents (protocol, host, port)
ORIGIN = ('http', 'localhost', 8080)

# debug mode enables more logging messages (in JS and console)
DEBUG = True

# HTTP Basic Authentication for complete website. None or ('user', 'pass').
AUTH = {
    'learning': None,
    'locked': None,
    'webinterface': None,  # override for web interface of the proxy
}

# URI path prefix for internal autoCSP URLs (webinterface)
WEBINTERFACE_URI = '_autoCSP'

# enable web interface in locked mode (only when AUTH['webinterface'] set)
LOCKED_WEBINTERFACE = True

# enabled interceptors (order matters)
INTERCEPTORS = (
    'auth',  # HTTP Basic Authentication - should stay at top
    'webinterface',  # exposes a webinterface
    'caching',  # disables caching in learning mode
    'csp',  # injects CSP
    #'hiddenproxy',  # sends faked HOST header (based on REVERSE_PROXY)
)

# logging format strings
LOG_FORMATS = {
    'CONSOLE': '%(asctime)s [%(name)s/%(levelname)s] %(message)s',
    'CONSOLE_DATE': '%H:%M:%S',
    'FILE': '%(asctime)s [%(name)s/%(levelname)s] %(message)s',
    'FILE_DATE': '%d.%m.%Y %H:%M',
}


PATHS = {
    # path to log file - leave empty to avoid logging to file
    'LOG': '',
    # path to sqlite3 database (does not have to exist)
    'DATABASE': 'proxy.sqlite',
    # path to all interceptor functions (w/ trailing slash)
    'INTERCEPTORS': 'interceptors/',
    # path to all View functions (w/ trailing slash)
    'VIEWS': 'webinterface/',
    # path to the CA certificate
    'CACERT': '~/.mitmproxy/mitmproxy-ca.pem',
}
