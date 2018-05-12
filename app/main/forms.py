#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 23:10
# @Author  : willis
# @Site    : 
# @File    : forms.py
# @Software: PyCharm

from flask import current_app

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError

from flask_pagedown.fields import PageDownField

from ..models import Role, User


class EditProfileForm(FlaskForm):
    name = StringField('姓名：', validators=[Length(0, 64)])
    location = StringField('地址：', validators=[Length(0, 64)])
    about_me = TextAreaField('介绍：')
    submit = SubmitField('提交')


class EditProfileAdminForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(),
                                          Length(1, 64), Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_]*$', 0,
               '用户名仅包含字母数字下划线')])
    confirmed = BooleanField('验证')
    role = SelectField('角色', coerce=int)
    name = StringField('姓名', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('介绍')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.role_name)
                             for role in Role.query.order_by(Role.role_name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已注册过.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用.')

    def validate_role(self, field):
        # 管理员权限
        admin = Role.query.filter_by(role_name='Administrator').first()
        if field.data == admin.id and self.email.data != current_app.config['FLASKY_ADMIN']:
            raise ValidationError('管理员权限只能授予特定的用户')


class PostForm(FlaskForm):
    body = PageDownField('输入内容：', validators=[DataRequired()])
    submit = SubmitField('提交')


class CommentForm(FlaskForm):
    body = StringField('评论', validators=[DataRequired()])
    submit = SubmitField('提交')

