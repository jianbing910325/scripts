#!/usr/bin/env python
# -*- coding:utf8 -*-

import paramiko
import logging
import os,sys
import gevent
from gevent.threadpool import ThreadPool

#格式化日志格式以及日志存储地址和文件mode(r,w,a)
logging.basicConfig(level=logging.INFO,
                format='%(asctime)s,%(filename)s,%(levelname)s,%(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='/tmp/command.log',
                filemode='w+')

class SSHClient(object):
    def __init__(self,host,passwd,user='root',port=22):
        self.ip = host
        self.port = port
        self.user = user
        self.passwd = passwd
        
    def command(self,command):
        """执行命令"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.host,
                        self.port,
                        username=self.user,
                        password=self.passwd,
                        timeout=30)
        except Exception as e:
            return u"%s: Connection fail!!! Error: %s"%(self.host,e)
        stdin,stdout,stderr = ssh.exec_command(command)
        ssh.close()
        return u"%s: %s"%(self.host,stdout.read().strip()+stderr.read().strip())

    def sync(self,local,remote):
        """上传文件"""
        ssh = paramiko.Transport("%s:%d"%(self.host,self.port))
        ssh.connect(username=self.user,password=self.passwd)
        sftp = paramiko.SFTPClient.from_transport(ssh,max_packet_size=64000)
        try:
            sftp.put(local,os.path.join(remote,os.path.basename(local)))
        except Exception as e:
            return '%s: %s upload faild,Error: %s'%(self.host,local,e)
        sftp.close()
        ssh.close()
        return '%s: upload success!'

def main():
    #创建线程池
    pool = ThreadPool(30)
    result = []
    #一个参数则用command
    if len(sys.argv) == 2:
        func = 'command'
    #两个参数则用sync
    if len(sys.argv) == 3:
        #判断本地文件
        if not os.path.isfile(sys.argv[1]):
            sys.stdout.write("This file is not in zhe system: %s"%sys.argv[1])
            sys.exit(1)
        func = 'sync'
    for i in open('iplist.txt'):
        s = SSHClient(*i.strip().split(","))
        #工厂模式处理
        result.append(pool.spawn(getattr(s,func),*sys.argv[1:]))
    #等待结束
    gevent.wait()
    for i in result:
        logging.info(i.get())

if __name__ == '__main__':
    main()
