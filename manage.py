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

from app import create_app, db
from app.models import User, Role, Post, Follow, Permission, Comment

from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand, upgrade


app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


# Shell中添加参数
# 现在的flask其实不在需要manager,自带run（runserver） db shell,目前暂时保留一下
# flask run
@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,
                Post=Post, Follow=Follow, Permission=Permission, Comment=Comment)

# manager 新版本已经不用
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))
manager.add_command('db', MigrateCommand)


@app.cli.command()
def runserver():
    app.run(host='0.0.0.0', port=5000)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')
def test(coverage):
    """运行测试"""
    # flask test --coverage
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


@app.cli.command()
@click.option('--length', default=25,
              help='Number of functions to include in the profiler report.')
@click.option('--profile-dir', default=None,
              help='Directory where profiler data files are saved.')
def profile(length, profile_dir):
    """性能测试：Start the application under the code profiler."""
    # flask profile -- --
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                      restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@app.cli.command()
def deploy():
    """部署"""

    # 把数据库迁移到最新修订版本
    upgrade()

    # 用户角色
    Role.update_roles()

    # 所有用户都关注自己
    User.add_self_follows()

if __name__ == '__main__':
    manager.run()
