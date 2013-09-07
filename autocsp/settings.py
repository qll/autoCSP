""" autoCSP configuration file. """

# Locked mode is one of the two modes of the autoCSP reverse HTTP proxy:
# Learning mode: When locked mode is disabled (False) the proxy will be in
#                learning mode. This mode is used to learn the benign structure
#                and markup of the site and build a Content Security Policy for
#                all document URIs. The site has to be browsed in this mode, so
#                that the proxy can collect violation reports and inject
#                JavaScript to generate a policy.
#                Warning: Please do not allow public access to the proxy in
#                learning mode. An attacker could loosen up the policies in
#                learning mode so that the policy could be useless.
# Locked mode: Locked mode can be enabled with setting the variable to True.
#              The proxy will enforce the policy built in learning mode on the
#              document URIs it knows. It tries to use a heuristic to detect
#              unknown but similar document URIs.
LOCKED_MODE = False


# The HTTP Origin of the server which should be protected.
# Tuple of (protocol, host, port).
# If proxying does not seem to work, please enable the hiddenproxy interceptor.
REVERSE_PROXY = ('http', 'localhost', 8000)


# HTTP Origin of autoCSP. The proxy needs its own address to build policies.
# Can be changed later on to protect the same ressource under a different URL.
ORIGIN = ('http', 'localhost', 8080)


# Debug mode enables more and more detailed logging messages.
DEBUG = True


# HTTP Basic Authentication credentials. None or ('user', 'pass').
AUTH = {
    'learning': None,  # Auth for the web app in learning mode.
    'locked': None,  # Auth for the web app in locked mode.
    'webinterface': None,  # Override auth for the web interface of the proxy.
}


# URI path prefix for internal autoCSP URLs (web interface).
WEBINTERFACE_URI = '_autoCSP'


# Enable web interface in locked mode (only when AUTH['webinterface'] set).
LOCKED_WEBINTERFACE = True


# Enabled interceptors (order matters).
INTERCEPTORS = (
    'caching',  # Disables caching in learning mode.
    'auth',  # HTTP Basic Authentication - should stay abvoe webinterface.
    'webinterface',  # Exposes a web interface.
    'csp',  # Injects CSPs into HTTP headers.
    #'hiddenproxy',  # Sends faked HOST header (based on REVERSE_PROXY).
)


# Logging format strings.
LOG_FORMATS = {
    'CONSOLE': '%(asctime)s [%(name)s/%(levelname)s] %(message)s',
    'CONSOLE_DATE': '%H:%M:%S',
    'FILE': '%(asctime)s [%(name)s/%(levelname)s] %(message)s',
    'FILE_DATE': '%d.%m.%Y %H:%M',
}


PATHS = {
    # Path to log file - leave empty to avoid logging to file.
    'LOG': '',
    # Path to sqlite3 database (does not have to exist).
    'DATABASE': 'proxy.sqlite',
    # Path to all interceptor functions (w/ trailing slash).
    'INTERCEPTORS': 'interceptors/',
    # Path to all View functions (w/ trailing slash).
    'VIEWS': 'webinterface/',
    # Path to the CA certificate.
    'CACERT': '~/.mitmproxy/mitmproxy-ca.pem',
}
