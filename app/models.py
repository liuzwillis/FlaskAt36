#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 23:15
# @Author  : willis
# @Site    : 
# @File    : models.py
# @Software: PyCharm

from flask import current_app

from flask_login import UserMixin

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from . import db, login_manager


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(64), unique=True)

    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = ['User', 'Moderator', 'Administrator']
        for r in roles:
            role = Role.query.filter_by(role_name=r).first()
            if role is None:
                role = Role(role_name=r)
                db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.role_name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # 继承一下父类的init
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def dumps_token(self, token_name, expiration=3600, **kwargs):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        data = {'token_name': token_name, 'user_id': self.id}
        data.update(kwargs)
        return s.dumps(data)

    @staticmethod
    def loads_token(token):
        # 解token，并验证user_id，否则返回None
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
            user_id = data.get('user_id')
            if user_id:     # and self.query.filter_by(id=user_id)
                return data
        except:
            return None

    def confirm(self, token):
        data = self.loads_token(token)
        if data.get('token_name') == 'confirm' and data.get('user_id') == self.id:
            self.confirmed = True
            db.session.add(self)
            return True

    def change(self):
        pass


# 加载用户的回调函数 见示例8.8
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
