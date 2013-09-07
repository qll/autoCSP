""" Object for sharing globally reachable objects (like database). """
# TODO(qll): Use dependency injection to remove the need for a global registry
from settings import LOCKED_MODE


class Globals(object):
    _vars = {}

    def __getitem__(self, key):
        """ Enables dict-like access: Globals()['key'] """
        return self._vars[key]

    def __setitem__(self, key, val):
        """ Enables dict-like access: Globals()['key'] = 1 """
        self._vars[key] = val


def assemble_origin(origin):
    if not isinstance(origin, (tuple, list)):
        return origin
    return '%s://%s%s' % (origin[0], origin[1], ':%d' % origin[2]
                                                if origin[2] != 80 else '')


def resolve_mode(mode):
    """ Resolves the mode of a event or webinterface view. """
    modes = ('*', 'locked', 'learning')
    if mode not in modes:
        raise ValueError('Mode can only be one of the following: %s' % modes)
    learn = True if mode in ('*', 'learning') else False
    locked = True if mode in ('*', 'locked') else False
    return (LOCKED_MODE and locked) or (not LOCKED_MODE and learn)
