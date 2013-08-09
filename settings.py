
# (schema, host, port) which will be reverse proxied
REVERSE_PROXY = ('http', 'localhost', 8000)

# URI path prefix for internal autoCSP URLs (webinterface)
WEBINTERFACE_URI = '_autoCSP'

# interceptors (order matters)
INTERCEPTORS = (
    'webinterface',
)

PATHS = {
    # path to all interceptor functions (w/ trailing slash)
    'INTERCEPTORS': 'interceptors/',
    # path to all View functions (w/ trailing slash)
    'VIEWS': 'webinterface/',
    # path to the CA certificate
    'CACERT': '~/.mitmproxy/mitmproxy-ca.pem',
}
