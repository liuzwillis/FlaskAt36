#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/13 013 18:39
# @Author  : willis
# @Site    : 
# @File    : test_client.py
# @Software: PyCharm

import re
import unittest
from app import create_app, db
from app.models import User, Role


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.update_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('陌生人'.encode() in response.data)

    def test_register_and_login(self):
        # 注册新用户
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertEqual(response.status_code, 302)

        # 使用新用户登录
        response = self.client.post('/auth/login', data={
            'username_or_email': 'john@example.com',
            'password': 'cat'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        text = response.data.decode()
        # print(text)
        self.assertTrue(re.search('您好,\s+john!', text))
        self.assertTrue(
            '您的邮箱还没有确认' in text)

        # send a confirmation token
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_token(token_name='confirm')
        response = self.client.get('/auth/confirm/{}'.format(token),
                                   follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            '邮箱验证成功' in response.data.decode())

        # 退出
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('您已注销' in response.data.decode())


if __name__ == '__main__':
    unittest.main()
