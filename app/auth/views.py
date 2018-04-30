#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/24 024 10:41
# @Author  : willis
# @Site    : 
# @File    : views.py
# @Software: PyCharm

from flask import render_template, redirect, url_for, request, flash

from flask_login import login_user, login_required, logout_user, current_user

from . import auth
from .forms import LoginForm, RegistrationForm,\
    ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm, ChangeEmailForm
from ..models import User
from .. import db
from ..email import send_email


@auth.before_app_request
def before_request():
    if current_user.is_authenticated\
            and not current_user.confirmed\
            and request.endpoint\
            and request.endpoint[:5] != 'auth.'\
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('您已经登录')
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('用户名或密码无效.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已注销.')
    return redirect(url_for('main.index'))


# 注册账户
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.dumps_token(token_name='confirm')
        send_email(user.email, '确认您的账户邮箱', 'auth/email/confirm', user=user, token=token)
        flash('我们已向您的邮箱发送了一封验证邮件，请及时验证。')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


# 验证 token
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('您已经验证过了')
    if current_user.confirm(token):
        flash('邮箱验证成功。')
    else:
        flash('验证链接无效或过期。')
    return redirect(url_for('main.index'))


# 重新发送验证邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.dumps_token(token_name='confirm')
    send_email(current_user.email, '确认您的邮箱',
               'auth/email/confirm', user=current_user, token=token)
    flash('我们已向您的邮箱发送了一封新的验证邮件.')
    return redirect(url_for('main.index'))

# # # 以下是管理账户的路由


# 登录状态下改密码
@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password(form.new_password)
            db.session.add(current_user)
            flash('您的密码修改成功')
            return redirect(url_for('main.index'))
        else:
            flash('旧密码错误')
    return render_template('auth/change_password.html', form=form)


# 忘记密码，未登录
@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_request():
    # 用户非登录状态才可以找回密码，这一设置是否合理？
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        # 表单validate 中已包含email验证，所以确定有该user
        user = User.query.filter_by(email=form.email.data).first()
        token = user.dumps_token(token_name='forgot_password')
        send_email(user.email, '重置密码', 'auth/email/forgot_password',
                   user=user, token=token, next=request.args.get('next'))
        # 上面一行多了一个next 理解不是很透彻
        flash('我们已向您的邮箱发送了一封邮件，请根据提示重置密码。')
        return redirect(url_for('main.index'))
    return render_template('auth/forgot_password_request.html', form=form)


# 忘记密码2 验证
@auth.route('/forgot-password-reset/<token>', methods=['GET', 'POST'])
def forgot_password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    data = User.loads_token(token)
    if data is None or data.get('token_name') != 'forget_password':
        flash('无效或过期的令牌')
        return redirect(url_for('main.index'))
    user = User.query.filter_by(id=data.get('user_id')).first()
    if user is None:
        flash('错误的令牌')
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password(form.password.data)
        flash('您的密码已重置，请登录')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password_reset.html',
                           username=user.username, form=form)


# 更换邮箱
@auth.route('/change-email-request', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            token = current_user.dumps_token(token_name='change_email',
                                             new_email=form.email.data)
            send_email(form.email.data, '确认您的新邮箱',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('我们已向您的邮箱发送了一封邮件，请在邮件指示下确认新邮箱')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误.')
    return render_template("auth/change_email_request.html", form=form)


# 更换邮箱2
@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    data = User.loads_token(token)
    # 验证data: token_name/user_id/new_email/
    if data is None\
            or data.get('token_name') != 'change_email'\
            or data.get('user_id') != current_user.id\
            or data.get('new_email') is None\
            or User.query.filter_by(email=data.get('new_email')).first() is not None:
            # 这里查一下new_email是必要的，防止用户会第二次使用url，虽然并不会引起什么大问题，但会造成困扰
        flash('无效或过期的令牌')
        return redirect(url_for('main.index'))
    current_user.email = data.get('new_email')
    flash('您的新邮箱已经验证成功')
    return redirect(url_for('main.index'))
