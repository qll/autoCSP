#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" CSP-injecting reverse HTTP proxy with policy auto-generation. """
import os

import lib.events
import lib.globals
import lib.sqlite
import settings

from libmproxy import proxy


def main():
    # change cwd to the directory of this file
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    paths = {k: os.path.expanduser(p) for k, p in settings.PATHS.items()}
    load_interceptors(paths['INTERCEPTORS'], settings.INTERCEPTORS)
    load_views(paths['VIEWS'])
    connect_to_db(paths['DATABASE'])
    config = proxy.ProxyConfig(cacert=paths['CACERT'],
                               reverse_proxy=settings.REVERSE_PROXY)
    server = proxy.ProxyServer(config, 8080)
    controller = lib.events.EventController(server)
    try:
        controller.run()
    except KeyboardInterrupt:
        controller.shutdown()
        lib.globals.Globals()['db'].close()


def connect_to_db(path):
    """ Connects to the sqlite3 database and initializes it if needed. """
    database_existed = os.path.isfile(path)
    lib.globals.Globals()['db'] = lib.sqlite.ThreadedDatabase(path)
    if not database_existed:
        lib.events.call('db_init')


def load_module(path):
    """ Loads any given module from a relative path. """
    if path.startswith('/'):
        raise ImportError('Cannot import absolute path "%s".' % path)
    if not os.path.isfile(path):
        raise ImportError('Cannot find module at "%s".' % path)
    head, tail = os.path.split(path)
    module, _ = os.path.splitext(tail)
    __import__('%s.%s' % ('.'.join(head.split('/')), module))


def load_interceptors(path, interceptors):
    """ Loads interceptors from a list to preserve order. """
    for i in interceptors:
        load_module('%s%s.py' % (path, i))


def load_views(path):
    """ Loads views from a folder and ignores all views prefixed with a _. """
    for view in os.listdir(path):
        if not view.startswith('_') and view.endswith('.py'):
            load_module(path + view)


if __name__ == '__main__':
    main()
