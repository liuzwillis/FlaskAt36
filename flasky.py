#!/usr/bin/python
# -*-coding:utf-8 -*-

import os
from threading import Thread

from flask import Flask
from flask import render_template
from flask import session, redirect, url_for
from flask import current_app
from flask import flash

from flask_script import Manager, Server, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_migrate import Migrate, MigrateCommand
from flask_mail import Mail, Message

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email

from flask_sqlalchemy import SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
# 设置密钥
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
# 设置调试模式
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
# 每次请求结束后将会自动提交数据库中的变动
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# 如果设置成 True，SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存，不必要可以禁用它。
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# email 配置
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER') or 'smtp.163.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
# 发件人的格式，可以写成tuple，flask_mail会识别
app.config['FLASKY_MAIL_SENDER'] = ('Flasky Admin', app.config['MAIL_USERNAME'])
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)


# 发送邮件
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    """
    发送异步邮件
    :param to: 收件人
    :param subject: 主题
    :param template: 模板文件
    :param kwargs: 模板的参数
    :return:
    """
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(64), unique=True)

    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.role_name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


# 添加命令行命令
# Server用于指定server的host等参数 python flasky.py runserver
# Shell 用于自动导入特定的对象 python flasky.py shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0', port=8080))
manager.add_command('db', MigrateCommand)


class NameForm(FlaskForm):
    name = StringField('你的名字：', validators=[DataRequired()])
    submit = SubmitField('提交')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/user', methods=['GET', 'POST'])
def user():
    form = NameForm()
    if form.validate_on_submit():
        user_ = User.query.filter_by(username=form.name.data).first()
        if user_ is None:
            user_ = User(username=form.name.data)
            db.session.add(user_)
            session['known'] = False
            # 如果有管理员，新用户注册时，给管理员发一个邮件，参数依次为，收件人、主题、模板、模板参数。
            # 163发送邮件其实很快，后面章节验证邮件会有坑，主要是因为163会判别带验证地址的邮件为垃圾邮件，而锁定ip或邮箱
            if app.config['FLASKY_ADMIN']:
                send_email(app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user_)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('user'))
    return render_template('user.html', form=form, name=session.get('name'), known=session.get('known', False))


@app.errorhandler(404)
def page_not_found2(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    manager.run()
