
rules = ('frame-src', 'img-src', 'script-src', 'style-src')


def generate_policy(directives):
    """ Generates policy from a directives dictionary looking like this:
        {'img-src': ['uri1', 'uri2'], 'style-src': ['uri'], ...} """
    policy = ['%s %s' % (d, ' '.join(directives.setdefault(d, ["'none'"])))
              for d in rules]
    # TODO(qll): Firefox does not know file path specific CSP directives, yet...
    return '; '.join(policy)
