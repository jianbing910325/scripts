#!/usr/bin/env python
# -*- coding:utf8 -*-

#wget http://www.moko.cc all pic

import re
import os,sys
import urllib2
import urllib
import gevent
from gevent.queue import Queue
from BeautifulSoup import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf8")

def index(url,search,headers):
    request = urllib2.Request(url,headers=headers)
    result = urllib2.urlopen(request)
    soup = BeautifulSoup(result)
    pattern = re.compile(u'[\u4E00-\u9FA5]')
    for i in soup.findAll("div",{"class": "vocation-mark"}):
        for j in i.contents:
            try:
                data = re.search("href=\"([^\"]+)\"",str(j)).group(1)
            except Exception as e:
                continue
            chinese = "".join(pattern.findall(str(j).decode("utf8")))
            if search.decode("gbk").encode("utf8") == chinese.encode("utf8"):
                return data

def page(iurl,headers):
    while not task1.empty():
        url = iurl+task1.get()
        request = urllib2.Request(url,headers=headers)
        result = urllib2.urlopen(request)
        soup = BeautifulSoup(result)
        for i in soup.findAll("div",{"class": "cover"}):
            for j in  i.findAll("a"):
                task2.put_nowait(j["href"])
        gevent.sleep(0)

def purl(url):
    task1.put_nowait(url)
    for i in range(2,21):
        temp = url.split("/")
        temp[-1] = str(i)+".html"
        url = "/".join(temp)
        task1.put_nowait(url)
        
def callback(blocknum, blocksize, totalsize):
    percent = 100.0 * blocknum * blocksize / totalsize
    if percent > 100:
        percent = 100
    print "%.2f%%"% percent
    
def download(iurl,headers):
    while not task2.empty():
        url = iurl+task2.get()
        request = urllib2.Request(url,headers=headers)
        result = urllib2.urlopen(request)
        soup = BeautifulSoup(result)
        for i in soup.findAll("p",{"class": "picBox"}):
            for j in i.findAll("img"):
                imgurl = j["src2"]
                try:
                    urllib.urlretrieve(imgurl,os.path.join(os.curdir,imgurl.split('/')[-1]),callback)
		except KeyboardInterrupt:
                    print u"退出下载"
                    sys.exit(1)
	gevent.sleep(0)    


if __name__ == "__main__":
    if not len(sys.argv[1]) == 2:
        sys.stdout.write(u"Usage: python %s 全部模特儿/化妆造型/设计插画/艺术/广告传媒/演义/游戏动漫/更多行业"%sys.argv[0])
        sys.exit(1)
    url = "http://www.moko.cc"
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36"}
    task1 = Queue()
    task2 = Queue()
    gevent.joinall([
        gevent.spawn(purl,index(url,sys.argv[1],headers)),
        gevent.spawn(page,url,headers),
        gevent.spawn(download,url,headers),
    ])
