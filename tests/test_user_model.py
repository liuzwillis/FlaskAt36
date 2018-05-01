#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/24 024 10:16
# @Author  : willis
# @Site    : 
# @File    : test_user_model.py
# @Software: PyCharm

import unittest
import time

from app import create_app, db
from app.models import User, Role, AnonymousUser, Permission


class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.update_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 密码

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    # token

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_token()
        self.assertTrue(u.loads_token(token) is not None)

    def test_expired_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_token(expiration=1)
        time.sleep(2)
        self.assertFalse(u.loads_token(token) is not None)

    def test_valid_loads_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_token(example='example')
        data = User.loads_token(token)
        self.assertTrue(data.get('token_name') == 'default')
        self.assertTrue(isinstance(data.get('user_id'), int))
        self.assertTrue(data.get('example') == 'example')

    def test_change_password(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        # 改密码
        self.assertTrue(u.change_password('cat', 'dog'))
        # 接着改第二次
        self.assertFalse(u.change_password('dog', 'horse'))
        # 旧密码错误
        self.assertFalse(u.change_password('tiger', 'horse'))
        pass

    def test_confirm_token(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token1 = u1.generate_token(token_name='others')
        token2 = u2.generate_token(token_name='confirm')
        token3 = u1.generate_token(token_name='confirm')
        # token类别错误
        self.assertFalse(u1.confirm(token1))
        # 他人的token
        self.assertFalse(u1.confirm(token2))
        self.assertTrue(u1.confirm(token3))

    def test_forgot_password_reset_token(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        user1 = User.query.filter_by(email='john@example.com').first()
        user2 = User.query.filter_by(email='susan@example.com').first()
        token1 = user1.generate_token(token_name='forgot_password')
        token2 = user2.generate_token(token_name='forgot_password')
        token3 = user1.generate_token(token_name='others')
        self.assertTrue(User.forgot_password_reset(token1, 'horse'))
        # 有效期内 可以使用多次
        self.assertTrue(User.forgot_password_reset(token1, 'horse2'))
        self.assertTrue(User.forgot_password_reset(token2, 'lion'))
        # token类别错误
        self.assertFalse(User.forgot_password_reset(token3, 'horse'))

    def test_change_email_token(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        # 其他类别
        token0 = u1.generate_token(token_name='others', new_email='john2@example.com')
        self.assertFalse(u1.change_email(token0))
        # 更改他人的邮箱/使用他人的token
        token1 = u1.generate_token(token_name='change_email', new_email='john2@example.com')
        self.assertFalse(u2.change_email(token1))
        # 试图使用已注册的邮箱
        token2 = u1.generate_token(token_name='change_email', new_email='susan@example.com')
        self.assertFalse(u1.change_email(token2))
        # 正确的使用
        token3 = u1.generate_token(token_name='change_email', new_email='john2@example.com')
        self.assertTrue(u1.change_email(token3))
        # token再次使用
        self.assertFalse(u1.change_email(token3))

    # role and permission 角色及权限

    def test_user_role(self):
        # 普通用户的权限
        # r = Role.query.filter_by(role_name='User').first()
        u = User(email='john@example.com', password='cat')
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_moderator_role(self):
        # 次级管理员的权限
        r = Role.query.filter_by(role_name='Moderator').first()
        u = User(email='john@example.com', password='cat', role=r)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_administrator_role(self):
        # admin权限
        r = Role.query.filter_by(role_name='Administrator').first()
        u = User(email='john@example.com', password='cat', role=r)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertTrue(u.can(Permission.ADMIN))

    def test_anonymous_user(self):
        # 无名游客的权限都是0
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_db_email_unique(self):
        # 现在数据库有一个问题，历史的原因，以前的email并不唯一，后来更新不上去了
        # 解决：打算drop_all,然后重新生成
        u1 = User(email='john@example.com', password='cat')
        with self.assertRaises(Exception):
            u2 = User(email='john@example.com', password='cat')
