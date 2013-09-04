
directives = ('connect-src', 'frame-src', 'img-src', 'media-src', 'object-src',
              'script-src', 'style-src')


def generate_policy(rules):
    """ Generates policy from a rules dictionary looking like this:
        {'img-src': ['uri1', 'uri2'], 'style-src': ['uri'], ...} """
    policy = ['%s %s' % (d, ' '.join(rules.setdefault(d, ["'none'"])))
              for d in directives]
    # TODO(qll): Firefox does not know file path specific CSP directives, yet...
    return '; '.join(policy)
