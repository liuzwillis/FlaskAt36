#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/24 024 1:41
# @Author  : willis
# @Site    : 
# @File    : test_basics.py
# @Software: PyCharm

import unittest

from flask import current_app
from app import create_app, db


# 简单的基本测试
class BasicsTestCase(unittest.TestCase):

    def setUp(self):
        # 创建测试用app
        self.app = create_app('testing')
        # 上下文，推送
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        # 移除
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])

