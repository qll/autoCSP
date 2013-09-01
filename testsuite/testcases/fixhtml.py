#!/usr/bin/env python2
""" Quick helper to add HTML5 DOCTYPE and <title> to every testcase. """
import os
import re
import sys


def fixhtml(folder):
    changed = 0
    for dirpath, _, filenames in os.walk(folder):
        for file in filenames:
            name, ext = os.path.splitext(file)
            if ext != '.html':
                continue
            path = '%s/%s' % (dirpath, file)
            title = ' '.join(name.split('-'))
            shouldbe = '<!DOCTYPE html>\n<title>%s</title>\n' % title
            with open(path, 'r') as f:
                content = f.read()
            if content.startswith(shouldbe):
                continue
            changed += 1
            content = re.sub('\s*<!DOCTYPE[^>]*>\s*<title>[^<]*</title>\s*', '',
                             content)
            with open(path, 'w') as f:
                f.write(shouldbe + content)
    return changed


if __name__ == '__main__':
    folder = '.' if len(sys.argv) < 2 else sys.argv[1]
    changed = fixhtml(folder)
    print('Fixed %d files.' % changed)
