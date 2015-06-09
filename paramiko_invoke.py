#!/usr/bin/env python
# -*- coding:utf8 -*-

import paramiko
import time

def sshclient(host,passwd,port=22,user='root'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host,port,user,passwd)
    chan = ssh.invoke_shell()
    while 1:
        comm = raw_input("[{0}@{1}]# ".format(user,host))
        if comm in ['exit','quit']:
            chan.send("exit\n")
            chan.close()
            break
        try:
            chan.send(comm+"\n")
        except Exception as e:
            chan = ssh.invoke_shell()
            continue
        time.sleep(1)
        data = chan.recv(4096)
        print "\n".join(data.split("\n")[1:-1])
    ssh.close()

if __name__ == "__main__":
    import sys
    sshclient(sys.argv[1],sys.argv[2])
