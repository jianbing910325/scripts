#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import base64
import pymongo
import tornado.httpserver
import tornado.web
import tornado.ioloop
import tornado.options

from uuid import uuid4
from tornado.options import options,define

define('port',default=80,help="port of tornado web",type=int)
define("dbhost",default="localhost",help="host of mongodb",type=str)
define("dbport",default=27017,help="port of mongodb",type=int)

class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            template_path = os.path.join(os.path.dirname(__file__),"templates"),
            static_path = os.path.join(os.path.dirname(__file__),"static"),
            cookie_secret = base64.b64encode(uuid4().bytes+uuid4().bytes),
            login_url = "/login",
            gzip = True,
            compress_response = True,
            autoreload = True)
        
        handlers = [
            (r'/',IndexHandler),
            (r'/login',LoginHandler),
            (r'/logout',LogoutHandler),
            (r'/(\w+)',PageHandler),
            (r'/action/(\w+)/(\w+)',ActionHandler)
            ]

        tornado.web.Application.__init__(self,handlers, **settings)
        conn = pymongo.MongoClient(options.dbhost,options.dbport)
        self.db = conn["test"]
        
class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *argc, **argkw):
	super(BaseHandler, self).__init__(*argc, **argkw)

    @property
    def db(self):
        return self.application.db
    
    def get_current_user(self):
        return self.get_secure_cookie("username")

    def write_error(self,status_code,**kwargs):
        if status_code == 404:
            self.wirte("404 Error Code")
        elif status_code == 500:
            self.write("500 Error Code")
        else:
            self.write("Error code: %s"%status_code)

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        self.set_secure_cookie("username",self.get_argument("username"))
        self.redirect("/")

class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("username")
        self.redirect("/login")
        
class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('index.html')

    @tornado.web.authenticated
    def post(self):
        self.write(self.request.body)

class PageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,method,data=""):
        if method in self.db.collection_names():
            data = self.db[method].find()
        try:
            self.render('%s.html'%method,data=data)
        except IOError:
            raise tornado.web.HTTPError(404)

class ActionHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self,table,method):
        data = dict(map(lambda x: x.split('='),self.request.body.split('&')))
        if method == 'create':
            self.application.db[table].insert_one(data)
        elif method == 'update':
            _id = data.pop('id')
            self.application.db[table].update_one({'_id': _id},data)
        elif method == 'delete':
            self.application.db[table].delete_one(data)
        self.redirect("/%s"%table)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
