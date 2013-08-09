import lib.http
import lib.webinterface

from lib.events import subscribe, EventPropagationStop
from settings import WEBINTERFACE_URI


def is_webinterface(path):
    """ Decides if URI is part of the webinterface given the path components.
    """
    return True if len(path) and path[0] == WEBINTERFACE_URI else False


@subscribe('response')
def ignore_webinterface(response):
    if is_webinterface(response.request.get_path_components()):
        raise EventPropagationStop()


@subscribe('request')
def handle_webinterface(request):
    path = request.get_path_components()
    if is_webinterface(path):
        response = lib.webinterface.call_view(request, '/' + '/'.join(path[1:]))
        request.reply(response.build(request))
        raise EventPropagationStop()
