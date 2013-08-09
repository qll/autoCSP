from lib.webinterface import path, make_response


@path('/')
def index(req):
    return make_response('layout.html')


@path('/test/(\d+)/(\w+)')
def test(req, num, word):
    return num + word
