from lib.webinterface import make_response, path


@path('/')
def index(req):
    return make_response('layout.html')
