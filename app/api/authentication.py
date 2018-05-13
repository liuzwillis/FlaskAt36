#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/13 013 10:52
# @Author  : willis
# @Site    : 
# @File    : authentication.py
# @Software: PyCharm

from operator import or_

from flask import g, jsonify

from flask_httpauth import HTTPBasicAuth

from ..models import User
from . import api
from .errors import unauthorized, forbidden

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    # 这里邮箱/用户名登录
    # user = User.query.filter_by(email=email_or_token).first()
    user = User.query.filter(or_(User.username == email_or_token,
                                 User.email == email_or_token)).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/tokens/', methods=['POST'])
def get_token():
    if g.current_user.is_anonymous or g.token_userd:
        return unauthorized('Invalid credentials')
    token = g.current_user.generate_token(token_name='auth', expiration=3600)
    return jsonify({'token': token, 'expiration': 3600})
