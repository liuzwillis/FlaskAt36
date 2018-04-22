#!/usr/bin/python
# -*-coding:utf-8 -*-

import os

from flask import Flask
from flask import render_template
from flask import session, redirect, url_for
from flask import flash

from flask_script import Manager, Server, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_migrate import Migrate, MigrateCommand

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email

from flask_sqlalchemy import SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
# 设置密钥
app.config['SECRET_KEY'] = 'hard to guess string123'
# 设置调试模式
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
# 每次请求结束后将会自动提交数据库中的变动
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# 如果设置成 True，SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存，不必要可以禁用它。
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


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


# class CommentForm(FlaskForm):
#     name = StringField('', validators=[Length(0, 64)], render_kw={"placeholder": "Your name",
#         "style": "background: url(/static/login-locked-icon.png) no-repeat 15px center;text-indent: 28px"})
#     email = StringField('', description='* We\'ll never share your email with anyone else.', validators= \
#         [DataRequired(), Length(4, 64), Email(message=u"邮件格式有误")], render_kw=
#         {"placeholder": "E-mail: yourname@example.com"})
#     comment = TextAreaField('', description=u"请提出宝贵意见和建议", validators=[DataRequired()],
#                             render_kw={"placeholder": "Input your comments here"})
#     test = StringField()
#     submit = SubmitField(u'提交')


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
    # 现在通过命令 python flask.py runserver 运行服务
