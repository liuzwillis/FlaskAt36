#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/24 024 0:03
# @Author  : willis
# @Site    : 
# @File    : manage.py
# @Software: PyCharm

import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

import sys
import click

from app import create_app
from app import db
from app.models import User, Role, Post, Follow, Permission, Comment

from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand


app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


# 添加命令行命令参数
# Server用于指定server的host等参数 python flasky.py runserver
# Shell 用于自动导入特定的对象 python flasky.py shell
@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,
                Post=Post, Follow=Follow, Permission=Permission, Comment=Comment)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))
manager.add_command('db', MigrateCommand)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')
def test(coverage):
    """运行测试"""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import subprocess
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(subprocess.call(sys.argv))

    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()

if __name__ == '__main__':
    manager.run()
