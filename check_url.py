#!/usr/bin/env python
# -*- coding:utf8 -*-

import requests
import sys
import gevent
from gevent.threadpool import ThreadPool

def Code_status(url):
    r = requests.get(url,timeout=5)
    if r.status_code == requests.codes.ok:
        return url

if __name__ == '__main__':
    pool = ThreadPool
    result = []
    for i in open('urlfile.txt'):
        result.append(pool.spawn(Code_status,i.strip()))
    for i in result:
        with open('saveurl.txt','a+') as f:
            f.write('%s OK!\n'%i.get())
