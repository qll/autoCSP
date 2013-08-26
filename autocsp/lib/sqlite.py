""" Slightly modified version of Louis Riviere's recipe
    http://code.activestate.com/recipes/526618/ (MIT license). """
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
            req, arg, res = self.requests.get()
            if req == '--close--':
                break
            try:
                cursor.execute(req, arg)
            except sqlite3.IntegrityError as e:
                self.lasterr = e
            connection.commit()
            if res:
                for record in cursor:
                    res.put(record)
                res.put('--no more--')
        connection.close()

    def execute(self, req, arg=None, res=None):
        self.requests.put((req, arg or tuple(), res))

    def select(self, req, arg=None):
        res = Queue()
        self.execute(req, arg, res)
        while True:
            rec = res.get()
            if rec == '--no more--':
                break
            yield rec

    def close(self):
        self.execute('--close--')
