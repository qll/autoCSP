import os

from lib.webinterface import Http404Error, Response, path
from settings import PATHS


# maps file endings to MIME-types
mime_types = {
    '': 'application/octet-stream',
    '.txt': 'text/plain',
    '.js': 'application/javascript',
    '.css': 'text/css',
}


@path('(/static/[\w\./]+)')
def static(req, path):
    """ Serves static files from the static directory. """
    views_path = os.path.expanduser(PATHS['VIEWS'])
    full_path = views_path + path[1:]
    # catch path traversal and check if file exists
    if len(os.path.normpath(path)) == 1 or not os.path.isfile(full_path):
        raise Http404Error()
    with open(full_path, 'r') as f:
        r = Response(content=f.read())
    _, ext = os.path.splitext(full_path)
    r.set_header('Content-Type', '%s; charset=UTF-8' %
                 mime_types.get(ext, mime_types['']))
    return r
