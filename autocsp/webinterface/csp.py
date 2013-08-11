from lib.webinterface import path


@path('/_/report')
def index(req):
    print(req.content)
    return ''
