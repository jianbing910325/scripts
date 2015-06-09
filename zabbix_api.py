#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = "lijianbing@leying365.com"

import json
import urllib2
import argparse
import sys

reload(sys)
sys.setdefaultencoding("utf8")

class zabbix_api(object):
    def __init__(self,url,user="Admin",passwd="zabbix"):
        self.url = url
        self.user = user
        self.passwd = passwd
        self.header = {"Content-Type":"application/json"}

    def user_login(self):
        data = json.dumps({
		"jsonrpc": "2.0",
		"method": "user.login",
		"params": {
			"user": self.user,
			"password": self.passwd
		},
		"id": 0
	})
        request = urllib2.Request(self.url,data,headers=self.header)
        try:
            result = urllib2.urlopen(request)
        except URLError as e:
            return u"url错误: %s，请检测！！！"%e
        response = json.loads(result.read())
        if not response.get("result"):
            return u"用户认证失败，请检查账号或者密码"
        else:
            result.close()
            self.authID = response.get("result")
            return self.authID

    def get(self,data):
        request = urllib2.Request(self.url,data,headers=self.header)
        result = urllib2.urlopen(request)
        response = json.loads(result.read())
        result.close()
        return response.has_key("result") and response["result"] or ""
    
    def host_get(self,hostname=''):
        data = json.dumps({
		"jsonrpc": "2.0",
		"method": "host.get",
		"params": {
			"output": "extend",
			"filter": {"host": hostname}
		},
		"auth": self.user_login(),
		"id": 1
	})
        res = self.get(data)
        print u"主机数量: %s"%len(res)
        if not len(res):
            return False
        status = {"0": "Monitored", "1": "Not Monitored"}
        available = {"0": "Unknown", "1": "Available", "2": "Unavailable"}
        for host in res:
            print u"主机ID: %s\t主机名: %s\t监控状态: %s\tagent连接状态: %s"\
                  %(host["hostid"],host["name"],status[host["status"]],available[host["available"]])
            self.hostId = host["hostid"]
        return self.hostId

    def group_get(self,groupname=''):
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": {
                        "output": "extend",
                        "filter": {"name": groupname.decode("gbk").encode("utf8")}
                },
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        print u"主机组数量: %s"%len(res)
        if not len(res):
            return False
        for group in res:
            print u"主机组ID: %s\t主机组名: %s"%(group["groupid"],group["name"])
            self.groupID = group["groupid"]
        return self.groupID

    def template_get(self,tempname=''):
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "template.get",
                "params": {
                        "output": "extend",
                        "filter": {"name": tempname}
                },
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        print u"模板数量: %s"%len(res)
        if not len(res):
            return False
        for template in res:
            print u"模板ID: %s\t 模板名称: %s"%(template["templateid"],template["name"])
            self.templateID = template["templateid"]
        return self.templateID

    def item_get(self,hostname):
        if not self.host_get(hostname):
            print u"该主机不存在"
            sys.exit(1)
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "item.get",
                "params": {
                        "output": "extend",
                        "hostids": self.host_get(hostname),
			"seach": {
			    "key_": "system"
			},
			"sortfield": "name"
                },
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        print u"这台主机共拥有%s个监控项"%len(res)
        status = {"0": "OK", "1": "Disabled"}
        for item in res:
            print u"监控项ID: %s\t监控项名称: %s\t监控项key: %s\t监控项状态: %s"\
                  %(item["itemid"],item["name"],item["key_"],status[item["status"]])

    def history_get(self,itemId):
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "history.get",
                "params": {
                        "output": "extend",
			"history": 0,
			"itemids": itemId,
			"sortfield": "clock",
			"sortorder": "DESC",
			"limit": 30
                },
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        for history in res:
            print u"监控项ID: %s\t时间: %s\t数据: %s\tNS: %s"\
                  %(history['itemid'],history['clock'],history['value'],history['ns'])
            
    def trigger_get(self,triggerid):
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "trigger.get",
                "params": {
                        "triggerids": triggerid,
                        "output": "extend",
                        "selectFunctions": "extend"
                },
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        if not len(res):
            return u"没有id为%s的触发器"%triggerid
        tr = res[0]
        func = tr["functions"][0]
        return u"函数{函数ID:%s  所属监控项ID:%s  函数名:%s  参数:%s} 触发器所属模板ID: %s\t触发器ID: %s\t表达式: %s\t优先级: %s\t描述: %s"\
               %(func["functionid"],func["itemid"],func["function"],func["parameter"],tr["templateid"],tr["triggerid"],tr["expression"],tr["priority"],tr["description"])

    def triggers_get(self):
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "trigger.get",
                "params": {
                        "output": [
                            "triggerid",
                            "description",
                            "priority"
                        ],
                        "filter": {
                            "value": 1
                        },
                        "sortfield": "priority",
                        "sortorder": "DESC"
                },
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        for trigger in res:
            print u"触发器ID: %s\t优先级: %s\t描述: %s"\
               %(trigger["triggerid"],trigger["priority"],trigger["description"])
    
    def group_create(self,groupname):
        if self.group_get(groupname):
            return u"这个主机组组%s已存在!!!"%groupname
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "hostgroup.create",
                "params": {
                        "output": "extend",
                        "filter": {"name": groupname}
                },
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        return u"添加主机组成功! 主机组ID：%s\t主机组: %s"%(res["groupids"],groupname)

    def host_create(self,hostname,aliasname,groupids,templateids):
        if self.host_get(hostname):
            return u"该主机%s已经添加!"%hostname
        data = json.dumps({
		"jsonrpc": "2.0",
    		"method": "host.create",
    		"params": {
        		"host": hostname,
			"name": aliasname.decode("gbk").encode("utf8"),
        		"interfaces": [
            		{
                	"type": 1,
                	"main": 1,
                	"useip": 1,
                	"ip": hostname,
                	"dns": "",
                	"port": "10050"
            		}],
			"groups": [{"groupid": i} for i in groupids.split(',')],
			"templates": [{"templateid": i} for i in templateids.split(',')]
		},
		"auth": self.user_login(),
		"id": 1
	})
        res = self.get(data)
        return u"添加主机成功! 主机ID: %s\t主机IP: %s\t主机名: %s"\
               %("".join(res["hostids"]),hostname,aliasname.decode("gbk").encode("utf8"))

    def host_update(self,hostname,templateids):
        data = json.dumps({
		"jsonrpc": "2.0",
                "method": "host.update",
                "params": {
			"hostid": self.host_get(hostname),
			"templates": [{"templateid": i} for i in templateids.split(',')],
		},
		"auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        if not res:
            return u"该主机不存在!"
        return u"主机修改成功! 主机ID: %s\t主机IP: %s"%("".join(res["hostids"]),hostname)

    def host_status(self,hostname,status=1):
        data = json.dumps({
		"jsonrpc": "2.0",
                "method": "host.update",
                "params": {
			"hostid": self.host_get(hostname),
			"status": status
		},
		"auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        if not res:
            return u"该主机不存在!"
        return status and u"该主机已经被停止监控!" or u"该主机启用监控!"
    
    def host_delete(self,hostids):
        data = json.dumps({
                "jsonrpc": "2.0",
                "method": "host.delete",
                "params": [{"hostid": i} for i in hostids],
                "auth": self.user_login(),
                "id": 1
        })
        res = self.get(data)
        if not res:
            return u"该主机不存在!"
        return u"删除的主机有%r"%(res["hostids"])
            
def main(url):
    api = zabbix_api(url)
    parser = argparse.ArgumentParser(description=u"""
这是一个调用zabbix api的python脚本。
使用方法如下(例子):
    python %(prog)s -H 10.100.0.1  *查看10.100.0.1这台主机状态

    python %(prog)s -AH  *查看所有的主机状态

    python %(prog)s -c 10.100.0.1 鼎新影院 1 10001 *创建一个主机，设置主机别名，分组，模板
""")
    parser.add_argument('-H','--host',nargs="?",dest='listhost',help=u"查看主机")
    parser.add_argument('-AH','--all-host',dest='allhost',action="store_true",help=u"显示所有主机")
    parser.add_argument('-G','--group',nargs="?",dest='listgroup',help=u"查看主机组")
    parser.add_argument('-AG','--all-group',dest='allgroup',action="store_true",help=u"显示所有主机组")
    parser.add_argument('-T','--template',nargs="?",dest="listtemplate",help=u"查看模板")
    parser.add_argument('-AT','--all-template',dest='alltemplate',action="store_true",help=u"显示所有模板")
    parser.add_argument('-I','--item',nargs="?",dest="listitem",metavar=('HOSTNAME'),help=u"查看某主机监控项")
    parser.add_argument('-O','--history',nargs="?",dest="history",metavar=('ITEMID'),help=u"查看某监控项的历史记录")
    parser.add_argument('-R','--trigger',nargs="?",dest="trigger",metavar=("Triggerid"),help=u"查看触发器信息")
    parser.add_argument('-AR','--triggers',dest='triggers',action="store_true",help=u"查看所有的触发器")
    parser.add_argument('-C','--add-group',nargs="?",dest='addgroup',help=u"创建新的主机组")
    parser.add_argument('-c','--add-host',nargs=4,dest='addhost',metavar=('HOSTNAME','ALIASNAME','8,10','10001,10002'),help=u"创建新的主机,多个主机组或模板用逗号分隔")
    parser.add_argument('-mc','--more-add-host',nargs="?",dest="moreaddhost",metavar=("FullPathFileName"),help=u"用文件，多线程添加主机(我这用的gevent协程)")
    parser.add_argument('-U','--update-host',nargs=2,dest="updatehost",metavar=("HOSTNAME","TEMPLATEID[,templateid]"),help=u"更新主机信息")
    parser.add_argument('-d','--disable-host',nargs=1,dest="disablehost",help="禁用主机")
    parser.add_argument('-e','--enable-host',nargs=1,dest="enablehost",help="启用主机")
    parser.add_argument('-D','--delete-host',nargs="+",dest="deletehost",help="删除主机，多个主机用空格分隔")
    parser.add_argument('-V','--version',action="version",version="zabbix api python 1.0.0",help="显示当前脚本版本")
    args = parser.parse_args()
    if args.listhost:
        api.host_get(args.listhost)
    elif args.allhost:
        api.host_get()
    elif args.listgroup:
        api.group_get(args.listgroup)
    elif args.allgroup:
        api.group_get()
    elif args.listtemplate:
        api.template_get(args.listtemplate)
    elif args.alltemplate:
        api.template_get()
    elif args.listitem:
        api.item_get(args.listitem)
    elif args.history:
        api.history_get(args.history)
    elif args.trigger:
        print api.trigger_get(args.trigger)
    elif args.triggers:
        api.triggers_get()
    elif args.addgroup:
        api.group_create(args.addgroup)
    elif args.addhost:
        host,name,groupids,templateids = args.addhost
        print api.host_create(host,name,groupids,templateids)
    elif args.updatehost:
        hostname,templateids = args.updatehost
        print api.host_update(hostname,templateids)
    elif args.disablehost:
        print api.host_status(args.disablehost)
    elif args.enablehost:
        print api.host_status(args.enablehost,status=0)
    elif args.deletehost:
        print api.host_delete(args.deletehost)
    elif args.moreaddhost:
        filename = args.moreaddhost
        import os.path
        import gevent
        #from gevent.queue import Queue
        if not os.path.exists(filename) or not os.path.isfile(filename):
            print u"当前目录没有找到此%s文件，可以选择输入绝对路径"
        #q = Queue()
        #def create():
        #    while not q.empty():
        #        host,name,groupids,templateids = q.get(block=False,timeout=5).split()
        #        gevent.sleep(0)
        #        print api.host_create(host,name,groupids,templateids)
        #def infile(name):
        #    for f in open(name):
        #        q.put_nowait(f.strip())
        #gevent.joinall([
        #    gevent.spawn(infile,filename),
        #    gevent.spawn(create),
        ])
        from gevent.threadpool import ThreadPool
        pool = Threadpool(30)
        for i in open(filename):
            pool.spawn(getattr(api,'host_create'),*i.strip().split(","))
        gevent.wait()
    else:
        parser.print_help()

if __name__ == "__main__":
    main("http://10.100.0.41/api_jsonrpc.php")
