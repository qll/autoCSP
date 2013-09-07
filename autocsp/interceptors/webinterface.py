import lib.http
import lib.webinterface

from lib.events import subscribe, EventPropagationStop


@subscribe('response', mode='learning')
def ignore_webinterface(response):
    if lib.webinterface.is_webinterface(response.request.get_path_components()):
        raise EventPropagationStop()


@subscribe('request', mode='learning')
def handle_webinterface(request):
    path = request.get_path_components()
    if lib.webinterface.is_webinterface(path):
        response = lib.webinterface.call_view(request, '/' + '/'.join(path[1:]))
        request.reply(response.build(request))
        raise EventPropagationStop()
