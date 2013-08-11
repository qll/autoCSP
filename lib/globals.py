""" Object for sharing globally reachable objects (like database). """
# TODO(qll): Use dependency injection to remove the need for a global registry


class Globals(object):
    _vars = {}

    def __getitem__(self, key):
        """ Enables dict-like access: Globals()['key'] """
        return self._vars[key]

    def __setitem__(self, key, val):
        """ Enables dict-like access: Globals()['key'] = 1 """
        self._vars[key] = val
