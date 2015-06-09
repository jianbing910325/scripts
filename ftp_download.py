#!/usr/bin/env python

import requests
import urllib,os
from multiprocessing import Pool,Queue
from BeautifulSoup import BeautifulSoup

def download_files(url,download_dir=None,n=4):
    res = requests.get(url)
    soup = BeautifulSoup(res.text)
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    for i in soup.findAll("a")[n:]:
        rurl = i["href"]
        if not rurl.endswith("/"):
            urllib.urlretrieve(res.url+rurl,os.path.join(download_dir,rurl))
        else:
            q.put((res.url+rurl,os.path.join(download_dir,rurl),n))

def main(queue):
    while True:
        if not queue.empty():
            url,download_dir,n = queue.get(block=False)
            download_files(url,download_dir,n)
        else:
            break

if __name__ == "__main__":
    q = Queue()
    q.put(("http://pkgs.repoforge.org/2hash/","E:\\2hash",5))
    p = Pool(10)
    p.apply_async(main,args=(q,))
    p.close()
    p.join()
    print "Done"
