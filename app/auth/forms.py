#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/28 028 12:40
# @Author  : willis
# @Site    : 
# @File    : forms.py
# @Software: PyCharm

import re

from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from ..models import User


class LoginForm(FlaskForm):
    # 用户名/邮箱登录
    # 用户名/邮箱的正则，前部分是username，后面是邮箱，忽略大小写
    username_email = StringField('用户名/邮箱：',
                                 validators=[DataRequired(),
                                             Length(1, 64),
                                             Regexp(r'(^[A-Za-z][A-Za-z0-9_]*$)|(^.+@([^.@][^@]+)$)',
                                                    0, '请输入正确的用户名/邮箱')])
    password = PasswordField('密码：', validators=[DataRequired(), Length(1, 64)])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    email = StringField('邮箱：', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名：', validators=[DataRequired(), Length(1, 64),
                                               Regexp('^[A-Za-z][A-Za-z0-9_]*$', 0,
                                                      '用户名以字母开头，可以使用字母数字或下划线')])
    password = PasswordField('创建密码：', validators=[DataRequired(), Length(1, 64),
                                                  EqualTo('password2', message='两次密码不一致')])
    password2 = PasswordField('确认密码：', validators=[DataRequired()])
    submit = SubmitField('注册')

    # validate后跟字段名，可以验证该字段名
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用')

# # # 以下是管理账户的表单


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码：', validators=[DataRequired()])
    new_password = PasswordField('新密码：', validators=[DataRequired(), Length(1, 64),
                                                     EqualTo('new_password2', message='两次密码不一致')])
    new_password2 = PasswordField('确认密码：', validators=[DataRequired()])
    submit = SubmitField('修改密码')


class ForgotPasswordForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('该邮箱未注册。')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message=u'两次输入不相同！')])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('重置密码')


class ChangeEmailForm(FlaskForm):
    email = StringField('新邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('更新邮箱')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已被注册.')

