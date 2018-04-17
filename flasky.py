#!/usr/bin/python
# -*-coding:utf-8 -*-

from flask import Flask
from flask import request
from flask import make_response
from flask_script import Manager, Server, Shell

app = Flask(__name__)
manager = Manager(app)


# 添加命令行命令
# Server用于指定server的host等参数 python flasky.py runserver
# Shell 用于自动导入特定的对象 python flasky.py shell
def make_shell_context():
    return dict(app=app)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0'))


@app.route('/')
def index():
    return '<p>hello world!</p>'


@app.route('/user/<name>')
def user(name):
    return '<p>hello {}!</p>'.format(name)


@app.route('/browser')
def browser():
    # 使用request上下文全局变量
    user_agent = request.headers.get('User-Agent')
    return '<p>Your browser is {}</p>'.format(user_agent)


@app.route('/cookie')
def cookie():
    response = make_response('<p>This document carries a cookie.</p>')
    response.set_cookie('answer', 42)
    return response


@app.errorhandler(404)
def page_not_found2(error):
    return '<p>page not found!</p>', 404


if __name__ == '__main__':
    manager.run()
    # 现在通过命令 python flask.py runserver 运行服务
