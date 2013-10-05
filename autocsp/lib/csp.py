import lib.utils

from settings import ORIGIN


directives = ('connect-src', 'font-src', 'form-action', 'frame-src', 'img-src',
              'media-src', 'object-src', 'script-src', 'style-src')


def generate_policy(rules):
    """ Generates policy from a rules dictionary looking like this:
        {'img-src': ['uri1', 'uri2'], 'style-src': ['uri'], ...} """
    policy = []
    origin = lib.utils.assemble_origin(ORIGIN)
    for d in directives:
        fixedrules = ["'none'"]
        if d in rules:
            fixedrules = [origin + r if r.startswith('/') else r
                          for r in rules[d]]
        policy.append('%s %s' % (d, ' '.join(fixedrules)))
    # TODO(qll): Firefox does not know file path specific CSP directives, yet...
    return '; '.join(policy)
