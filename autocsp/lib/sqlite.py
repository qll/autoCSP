""" Slightly modified version of Louis Riviere's recipe
    http://code.activestate.com/recipes/526618/ (MIT license). """
import logging
import sqlite3
import threading

from Queue import Queue


class ThreadedDatabase(threading.Thread):
    def __init__(self, path):
        super(ThreadedDatabase, self).__init__()
        self.path = path
        self.requests = Queue()
        self.lasterr = None
        self.start()

    def run(self):
        connection = sqlite3.connect(self.path)
        cursor = connection.cursor()
        while True:
            try:
                req, arg, res = self.requests.get()
                if req == '--close--':
                    break
                cursor.execute(req, arg)
                connection.commit()
                if res:
                    for record in cursor:
                        res.put(record)
                    res.put('--no more--')
            except Exception as e:
                logging.getLogger(__name__).exception(e)
        connection.close()

    def execute(self, req, arg=None, res=None):
        if arg:
            if not isinstance(arg, (tuple, dict)):
                arg = (arg,)
        else:
            arg = tuple()
        self.requests.put((req, arg, res))

    def select(self, req, arg=None):
        res = Queue()
        self.execute(req, arg, res)
        while True:
            rec = res.get()
            if rec == '--no more--':
                break
            yield rec

    def get_all(self, req, arg=None):
        return [r for r in self.select(req, arg)]

    def count(self, what, arg=None):
        result = self.get_all('SELECT COUNT(id) FROM ' + what, arg)
        return result[0][0]

    def fetch_one(self, req, arg=None):
        try:
            return self.select(req, arg).next()
        except StopIteration:
            return None

    def close(self):
        self.execute('--close--')
