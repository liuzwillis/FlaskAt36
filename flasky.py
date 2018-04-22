#!/usr/bin/python
# -*-coding:utf-8 -*-

from flask import Flask
from flask import render_template
from flask import session, redirect, url_for
from flask import flash

from flask_script import Manager, Server, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment

from flask_wtf import FlaskForm
from wtforms import StringField,TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email


app = Flask(__name__)
# 设置密钥
app.config['SECRET_KEY'] = 'hard to guess string123'
# 设置调试模式
app.config['DEBUG'] = True

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)


# 添加命令行命令
# Server用于指定server的host等参数 python flasky.py runserver
# Shell 用于自动导入特定的对象 python flasky.py shell
def make_shell_context():
    return dict(app=app)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('runserver', Server(host='0.0.0.0', port=8080))


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
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('名字已改变')
        # 将原来的name添加都session中记录
        session['name'] = form.name.data
        return redirect(url_for('user'))
    return render_template('user.html', form=form, name=session.get('name'))


@app.errorhandler(404)
def page_not_found2(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    manager.run()
    # 现在通过命令 python flask.py runserver 运行服务

