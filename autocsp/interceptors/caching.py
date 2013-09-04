from lib.events import subscribe


@subscribe('response', mode='learning')
def disable_caching(resp):
    """ Strips caching headers and adds cache prevention in learning mode. """
    for field in ('ETag', 'Last-Modified'):
        if field in resp.headers:
            del resp.headers[field]
    resp.headers['Expires'] = ['-1']
    resp.headers['Pragma'] = ['no-cache']
    resp.headers['Cache-Control'] = ['no-cache, no-store, must-revalidate']
