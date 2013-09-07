#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" CSP-injecting reverse HTTP proxy with policy auto-generation. """
import logging
import optparse
import os

import lib.events
import lib.utils
import lib.sqlite
import settings

from libmproxy import proxy


def main():
    try:
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
        set_up_logging(settings.DEBUG, options.daemonize, paths['LOG'],
                       settings.LOG_FORMATS)
        logging.info('Starting in %s mode.' % ('locked' if settings.LOCKED_MODE
                                                        else 'learning'))
        load_interceptors(paths['INTERCEPTORS'], settings.INTERCEPTORS)
        logging.debug('Interceptors loaded.')
        load_views(paths['VIEWS'])
        logging.debug('Views loaded.')
        connect_to_db(paths['DATABASE'])
        logging.debug('Connected to database.')
        config = proxy.ProxyConfig(cacert=paths['CACERT'],
                                   reverse_proxy=settings.REVERSE_PROXY)
        server = proxy.ProxyServer(config, settings.ORIGIN[2])
        controller = lib.events.EventController(server)
        logging.info('Reverse proxy available at %s/' %
                     lib.utils.assemble_origin(settings.ORIGIN))
        controller.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception(e)
    finally:
        logging.info('Shutting down.')
        try:
            controller.shutdown()
        except:
            pass
        try:
            lib.utils.Globals()['db'].close()
        except:
            pass
        logging.shutdown()


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
    db = lib.sqlite.ThreadedDatabase(path)
    lib.utils.Globals()['db'] = db
    if not database_existed:
        lib.events.call('db_init', db)


def load_module(path):
    """ Loads any given module from a relative path. """
    if path.startswith('/'):
        raise ImportError('Cannot import absolute path "%s".' % path)
    if not os.path.isfile(path):
        raise ImportError('Cannot find module at "%s".' % path)
    head, tail = os.path.split(path)
    module, _ = os.path.splitext(tail)
    __import__('%s.%s' % ('.'.join(head.split('/')), module))


def set_up_logging(debug, daemonized, log_file, format):
    """ Sets up the logging module. """
    if '/' in log_file:
        path = os.path.split(log_file)[0]
        # create log directory if not exists, yet
        if not os.path.isdir(path):
            os.makedirs(path)
    logging.logMultiprocessing = 0
    logging.logProcesses = 0
    logging.logThreads = 0
    # get root logger and configure it
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if not daemonized:
        # no logging to console when daemonized
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(format['CONSOLE'], format['CONSOLE_DATE'])
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(format['FILE'], format['FILE_DATE'])
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


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
