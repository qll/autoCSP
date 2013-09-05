""" Stupid and slow Alexa crawler for statistics purposes. """
import datetime
import os
import requests
import sqlite3
import sys


CSVFILE = 'top-1m.csv'
HOWMANY = 1000
DBNAME = 'top{0}_{1}.sqlite'.format(HOWMANY,
                                    datetime.date.today().strftime('%d-%m-%Y'))
USERAGENT = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like '
             'Gecko) Chrome/28.0.1500.95 Safari/537.36')


def connect_or_create_db(dbname):
    existed = os.path.isfile(dbname)
    db = sqlite3.connect(dbname)
    if not existed:
        db.execute('CREATE TABLE pages (rank INTEGER PRIMARY KEY, '
                   'url TEXT, content TEXT)')
        db.execute('CREATE TABLE headers (id INTEGER PRIMARY KEY, '
                   'page_id INTEGER, field TEXT, value TEXT)')
    return db


def read_urls(csvfile, howmany):
    """ Expects a CSV file in the format "rank,url\nrank,url\n..." """
    with open(csvfile, 'r') as f:
        i = 0
        urls = []
        for line in f:
            if (i >= howmany):
                break
            urls.append(line.strip().split(','))
            i += 1
    return urls


def main(csvfile, howmany, dbname, ua):
    urls = read_urls(csvfile, howmany)
    db = connect_or_create_db(dbname)
    print('[-] Crawling top {0} URLs.'.format(howmany))
    for rank, url in urls:
        print('[ ] Getting ({0}, {1})'.format(rank, url))
        try:
            r = requests.get('http://{0}/'.format(url), headers={'User-Agent':
                                                                 ua})
            if r.status_code == 200:
                db.execute('INSERT INTO pages VALUES (?, ?, ?)', (rank, url,
                                                                  r.text))
                for field, value in r.headers.items():
                    db.execute('INSERT INTO headers VALUES (NULL, ?, ?, ?)',
                               (rank, field, value))
                db.commit()
            else:
                print('[!] Bad status code')
        except KeyboardInterrupt:
            break
        except:
            print("[!] That thing error'd.")
    print('[-] Work done!')


if __name__ == '__main__':
    csvfile = CSVFILE if len(sys.argv) < 2 else sys.argv[1]
    main(csvfile, HOWMANY, DBNAME, USERAGENT)
