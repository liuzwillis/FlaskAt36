#!/usr/bin/python
# -*-coding:utf-8 -*-

from flask import Flask
from flask import request
from flask import make_response
from flask import render_template
from datetime import datetime

from flask_script import Manager, Server, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


# 添加命令行命令
# Server用于指定server的host等参数 python flasky.py runserver
# Shell 用于自动导入特定的对象 python flasky.py shell
def make_shell_context():
    return dict(app=app)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0'))


@app.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_not_found2(error):
    return '<p>page not found!</p>', 404


if __name__ == '__main__':
    manager.run()
    # 现在通过命令 python flask.py runserver 运行服务
