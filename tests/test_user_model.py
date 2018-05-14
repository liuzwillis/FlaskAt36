#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/24 024 10:16
# @Author  : willis
# @Site    : 
# @File    : test_user_model.py
# @Software: PyCharm

import unittest
import time

from datetime import datetime

from app import create_app, db
from app.models import User, Role, AnonymousUser, Permission, Follow


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
        self.assertTrue(u.change_password('dog', 'horse'))
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
        # 邮箱独一性，unique
        # 现在(以前)数据库有一个问题，历史的原因，以前的email并不唯一，后来更新不上去了
        # 解决：打算drop_all,然后重新生成
        u1 = User(email='john@example.com', password='cat')
        db.session.add(u1)
        db.session.commit()
        with self.assertRaises(Exception):
            u2 = User(email='john@example.com', password='cat2')
            db.session.add(u2)
            db.session.commit()

    def test_timestamps(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        self.assertTrue(
            (datetime.utcnow() - u.member_since).total_seconds() < 3
        )
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 3
        )

    def test_ping(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_gravatar(self):
        u = User(email='john@example.com', password='cat')
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar_256 = u.gravatar(size=256)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')
        self.assertTrue('https://secure.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6' in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)

    def test_follows(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        timestamp_before = datetime.utcnow()
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.followed.count() == 2)
        self.assertTrue(u2.followers.count() == 2)
        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2)
        self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
        f = u2.followers.all()[-1]
        self.assertTrue(f.follower == u1)
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)

    def test_to_json(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        with self.app.test_request_context('/'):
            json_user = u.to_json()
        expected_keys = ['url', 'username', 'member_since', 'last_seen',
                         'posts_url', 'followed_posts_url', 'post_count']
        self.assertEqual(sorted(json_user.keys()), sorted(expected_keys))
        self.assertEqual('/api/v1/users/' + str(u.id), json_user['url'])
