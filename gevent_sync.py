#!/usr/bin/env python
# -*- coding:utf8 -*-

import paramiko
import logging
import os,sys
import gevent
from gevent.threadpool import ThreadPool

logging.basicConfig(level=logging.INFO,
                format='%(asctime)s,%(filename)s,%(levelname)s,%(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='rsync.log',
                filemode='a+')

def sync(host,local_path,remote_path,user='root',passwd='123456'):
    ssh = paramiko.Transport("%s:22"%host)
    ssh.connect(username=user,password=passwd)
    sftp = paramiko.SFTPClient.from_transport(ssh,max_packet_size=64000)
    for root,dirs,files in os.walk(local_path):
        for d in dirs:
            local_dir = os.path.join(root,d)
            path = local_dir.replace(local_path,'').replace('\\','/')
            remote_dir = remote_path+path
            try:
                sftp.mkdir(remote_dir)
            except Exception as e:
                logging.warn('%s: %s create dir fail!check!'%(host,remote_dir))
                return '%s-%s'%(remote_dir,e)
            logging.info('%s: %s dir is create'%(host,remote_dir))
        for f in files:
            local_file = os.path.join(root,f)
            path = local_file.replace(local_path,'').replace('\\','/')
            remote_file = remote_path+path
            try:
                sftp.put(local_file,remote_file)
            except Exception as e:
                logging.warn('%s: %s upload file fail!'%(host,remote_file))
                return '%s'%e
            logging.info("%s: upload %s to remote %s"%(host,local_file,remote_file))
    sftp.close()
    ssh.close()
    logging.info("%s: upload all file success"%host)
    return 'upload all file success'

if __name__ == '__main__':
    pool = ThreadPool(30)
    local_dir = sys.argv[1]
    remote_dir = sys.argv[2]
    if not os.path.exists(local_dir) and not os.path.isdir(local_dir):
        sys.stdout.write('not find the dir: %s'%local_dir)
        sys.exit(1)
    for i in open('iplist.txt'):
        pool.spawn(sync,i.strip(),local_dir,remote_dir)
    gevent.wait()
