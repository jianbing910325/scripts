#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = "lijianbing@leying365.com"

import json
import requests
import argparse
import sys

reload(sys)
sys.setdefaultencoding("utf8")

class ZabbixException(Exception):
    pass


class Zabbix_Api(object):
    def __init__(self,url,user=None,passwd=None,timeout=30):
        self.url = url+"/api_jsonrpc.php"

        self.username = user
        self.password = passwd

        self.auth = ''
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({"Content-Type":"application/json",
                                     "User-Agent": "Python/zabbix_api"
                                     })

    def login(self):
        self.auth = self.zabbix_request("user","login",{"user":self.username,"password":self.password})["result"]

    def host_id(self,hostname):
        result = self.zabbix_request("host","get",{"output": "hostid","filter": {"host": hostname}})["result"]
        return result[0]["hostid"]
        
    def zabbix_request(self,method1,method2,params=None):
        request_json = {"jsonrpc": "2.0",
                        "method": "%s.%s"%(method1,method2),
                        "params": params or {},
                        "id": self.auth and 1 or 0
                        }
        if self.auth:
            request_json.update({"auth": self.auth})
        
        response = self.session.post(self.url,
                                     data = json.dumps(request_json),
                                     timeout = self.timeout
                                     )

        response.raise_for_status()

        if not len(response.text):
            raise ZabbixException("Returns an empty response")

        try:
            response_json = response.json()
        except ValueError:
            raise ZabbixException("Unable to parse json: %s"%response.json())

        if 'error' in response_json:
            if 'data' not in response_json['error']:
                response_json['error']['data'] = "No data"
            msg = "Error {code}: {message} , {data} while sending {json}".format(
                code = response_json['error']['code'],
                message = response_json['error']['message'],
                data = response_json['error']['data'],
                json = str(request_json))
            raise ZabbixException(msg,response_json['error']['code'])
        return response_json
    
    def __getattr__(self,attr1):
        def func(attr2,params=None):
            return self.zabbix_request(attr1,attr2,params)["result"]
        return func
            
def main(url,user=None,password=None):
    api = Zabbix_Api(url,user=user,passwd=password)
    api.login()
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
    parser.add_argument('-I','--item',nargs="?",dest="listitem",metavar=('HOSTNAME'),help=u"查看某主机监控项(跟主机ID)")
    parser.add_argument('-O','--history',nargs="?",dest="history",metavar=('ITEMID'),help=u"查看某监控项的历史记录(跟监控项ID)")
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
    status = {"0": "Monitored", "1": "Not Monitored"}
    available = {"0": "Unknown", "1": "Available", "2": "Unavailable"}
    if args.listhost:
        data = api.host("get",{"output": "extend","filter": {"host": args.listhost}})
        for host in data:
            print u"主机ID: {}\t主机名: {}\t监控状态: {}\tagent连接状态: {}".format(
                host["hostid"],host["name"],status[host["status"]],available[host["available"]])
    elif args.allhost:
        data = api.host("get",{"output": "extend"})
        for host in data:
            print u"主机ID: {}\t主机名: {}\t监控状态: {}\tagent连接状态: {}".format(
                host["hostid"],host["name"],status[host["status"]],available[host["available"]])
    elif args.listgroup:
        data = api.hostgroup("get",{"output": "extend","filter": {"name":args.listgroup}})
        for group in data:
            print u"主机组ID: {}\t主机组名: {}".format(group["groupid"],group["name"])
    elif args.allgroup:
        data = api.hostgroup("get",{"output": "extend"})
        for group in data:
            print u"主机组ID: {}\t主机组名: {}".format(group["groupid"],group["name"])
    elif args.listtemplate:
        data = api.template("get",{"output": "extend","filter": {"name":args.listtemplate}})
        for template in data:
            print u"模板ID: {}\t模板名称: {}".format(template["templateid"],template["name"])
    elif args.alltemplate:
        data = api.template("get",{"output": "extend"})
        for template in data:
            print u"模板ID: {}\t模板名称: {}".format(template["templateid"],template["name"])
    elif args.listitem:
        status = {"0": "OK", "1": "Disabled"}
        data = api.item("get",{"output": "extend","hostids": args.listitem,"seach": {"key_": "system"},"sortfield": "name"})
        for item in data:
            print u"监控项ID: {}\t监控项名称: {}\t监控项key: {}\t监控项状态: {}".format(
                  item["itemid"],item["name"],item["key_"],status[item["status"]])
    elif args.history:
        data = api.histroy("get",{"output": "extend",
                                  "history": 0,
                                  "itemids": args.histroy,
                                  "sortfield": "clock",
                                  "limit": 30})
        for history in data:
            print u"监控项ID: {}\t时间: {}\t数据: {}\tNS: {}".format(
                  history['itemid'],history['clock'],history['value'],history['ns'])
    elif args.trigger:
        data = api.trigger("get",{"triggerids": ags.trigger,"output": "extend","selectFunctions": "extend"})
        func = data[0]["functions"][0]
        print u"函数{函数ID:%s  所属监控项ID:%s  函数名:%s  参数:%s} 触发器所属模板ID: %s\t触发器ID: %s\t表达式: %s\t优先级: %s\t描述: %s"\
               %(func["functionid"],func["itemid"],func["function"],func["parameter"],tr["templateid"],tr["triggerid"],tr["expression"],tr["priority"],tr["description"])
    elif args.triggers:
        data = api.trigger("get",{"output": ["triggerid","description","priority"],
                                  "filter": {"value": 1},
                                  "sortfield": "priority",
                                  "sortorder": "DESC"})
        for trigger in data:
            print u"触发器ID: {}\t优先级: {}\t描述: {}".format(
               trigger["triggerid"],trigger["priority"],trigger["description"])
    elif args.addgroup:
        data = api.hostgroup("create",{"output": "extend","filter": {"name": args.addgroup}})
        print u"添加主机组成功! 主机组ID：%s\t主机组: %s"%(data["groupids"],args.addgroup)
    elif args.addhost:
        host,name,groupids,templateids = args.addhost
        data = api.host("create",{"host": host,
                                  "name": name.decode('gbk').encode('utf8'),
                                  "interfaces": [{
                                      "type": 1,
                                      "main": 1,
                                      "useip": 1,
                                      "ip": host,
                                      "dns": "",
                                      "port": "10050"}],
                                  "groups": map(lambda x:{"groupid": x},groupids.split(',')),
                                  "templates": map(lambda x: {"templateid": x},templateids.split(','))})
        print u"添加主机成功! 主机ID: {}\t主机IP: {}\t主机名: {}".format(
            "".join(data["hostids"]),host,name.decode("gbk").encode("utf8"))
    elif args.updatehost:
        hostname,templateids = args.updatehost
        data = api.host("update",{"hostid": api.host_id(hostname),
                                  "templates": map(lambda x: {"templateid": x},templateids.split(','))})
        if not data:
            print u"该主机不存在!"
            sys._exit(1)
        print u"主机修改成功! 主机ID: {}\t主机IP: {}".format("".join(data["hostids"]),hostname)
    elif args.disablehost:
        data = api.host("update",{"hostid": api.host_id(args.disablehost),"status": 1})
        if not data:
            print u"该主机不存在!"
            sys._exit(1)
        print "该主机(%s)已经被停止监控!"%args.disablehost
    elif args.enablehost:
        data = api.host("update",{"hostid": api.host_id(args.disablehost),"status": 0})
        if not data:
            print u"该主机不存在!"
            sys._exit(1)
        print "该主机(%s)已经启用监控!"%args.disablehost
    elif args.deletehost:
        data = api.host("delete",map(lambda x: {"hostid": x},map(lambda y: api.host_id(y),args.deletehost)))
        print "删除的主机有%r"%(data["hostids"])
        
    elif args.moreaddhost:
        filename = args.moreaddhost
        import os.path
        import gevent
        if not os.path.exists(filename) or not os.path.isfile(filename):
            print u"当前目录没有找到此%s文件，可以选择输入绝对路径"
        from gevent.threadpool import ThreadPool
        pool = Threadpool(30)
        for i in open(filename):
            host,name,groupids,templateids = i.strip().split(",")
            pool.spawn(api.host,"get",{"host": host,
                                  "name": name,
                                  "interfaces": [{
                                      "type": 1,
                                      "main": 1,
                                      "useip": 1,
                                      "ip": host,
                                      "dns": "",
                                      "port": "10050"}],
                                  "groups": map(lambda x:{"groupid": x},groupids.split(',')),
                                  "templates": map(lambda x: {"templateid": x},templateids.split(','))})
        gevent.wait()
        print u"主机全部添加完毕!"
    else:
        parser.print_help()

if __name__ == "__main__":
    main("http://10.100.0.41",user='admin',password='admin')
