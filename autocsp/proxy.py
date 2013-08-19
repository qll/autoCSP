#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" CSP-injecting reverse HTTP proxy with policy auto-generation. """
import optparse
import os

import lib.events
import lib.globals
import lib.sqlite
import settings

from libmproxy import proxy


def main():
    options = get_options()
    if options.daemonize:
        daemonize()
    # change cwd to the directory of this file
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # create files with 600 and dirs with 700 permissions (63 = 077)
    os.umask(63)
    if options.pid != None:
        write_pid_file(options.pid)
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


def get_options():
    """ Parses command line options and returns a dictionary containing the
        results. """
    parser = optparse.OptionParser()
    parser.add_option('-d', '--daemonize', action='store_true', default=None,
                      help='daemonize autoCSP (fork to background process)')
    parser.add_option('-p', '--pid', default=None,
                      help='create file with process ID at given path')
    return parser.parse_args()[0]


def daemonize():
    """ Forks the program to the background and closes all file descriptors. """
    fork()
    os.setsid()
    fork()
    # close file descriptors
    for fd in range(3):
        try:
            os.close(fd)
        except OSError:
            pass
    # open /dev/null as filedescriptor
    os.open(os.devnull, os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)


def fork():
    """ Forks and kills parent. """
    pid = os.fork()
    if pid > 0:
        os._exit(0)


def write_pid_file(path):
    """ Writes a file with the process ID to the file system. """
    with open(path, 'w') as f:
        f.write(str(os.getpid()))


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
