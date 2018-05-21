#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/14 014 9:36
# @Author  : willis
# @Site    : 
# @File    : test_selenium.py
# @Software: PyCharm

import unittest
from selenium import webdriver
import threading, time, re
import os
from app import create_app, db
from app import fake
from app.models import Role, User


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # 开启 火狐浏览器 无界面模式 关闭显卡加速
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        try:
            # 如果在win10环境下，根据路径找到软件
            if os.name == 'nt':
                cls.client = webdriver.Firefox(executable_path=r'D:\Program Files\geckodriver\geckodriver.exe',
                                               firefox_options=options)
            else:
                cls.client = webdriver.Firefox(firefox_options=options)
        except Exception as e:
            print(e)
            pass

        # 如果无法启动浏览器，跳过这些测试
        if cls.client:
            # 创建程序
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # 禁止日志，保持输出的清洁
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel('ERROR')

            # 创建数据库，并使用一些虚拟数据填充
            db.create_all()
            Role.update_roles()
            fake.users(30)
            fake.posts(30)

            # 添加管理员
            admin_role = Role.query.filter_by(role_name='Administrator').first()
            admin = User(email='john@example.com', username='john', password='cat', role=admin_role, confirmed=True)
            db.session.add(admin)
            db.session.commit()

            # 在一个线程中启动flask服务器
            cls.server_thread = threading.Thread(target=cls.app.run, kwargs={'debug': False})
            cls.server_thread.start()
            # 睡一秒，确保服务器已经开启
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # 关闭flask服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # 销毁数据库
            db.drop_all()
            db.session.remove()

            # 删除程序上下文
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        # 进入首页
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('你好\s+陌生人',
                                  self.client.page_source))

        # 进入登录页面
        self.client.find_element_by_link_text('登录').click()
        self.assertIn('<h1>登录</h1>', self.client.page_source)

        # 用email登录
        self.client.find_element_by_name('username_or_email'). \
            send_keys('john@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        self.assertTrue(re.search('你好\s+john', self.client.page_source))

        # print(self.client.page_source)
        # 进入用户资料页面出现错误，没有找到指定的连接，所以进行一些其他测试，试图找到原因所在
        # 错误原因找到，个人资料选项在下拉菜单中，需要先点击才能找到
        self.client.find_element_by_link_text('john').click()
        # 退出
        self.client.find_element_by_link_text('退出').click()

        # # 重新以username登录
        # self.client.find_element_by_link_text('登录').click()
        # self.client.find_element_by_name('username_or_email').send_keys('john')
        # self.client.find_element_by_name('password').send_keys('cat')
        # self.client.find_element_by_name('submit').click()
        # self.assertTrue(re.search('你好\s+john', self.client.page_source))
        #
        # # 进入用户资料页面
        # self.client.find_element_by_link_text('john').click()
        # self.client.find_element_by_link_text('个人资料').click()
        # self.assertIn('<h1>john</h1>', self.client.page_source)
        # # 编辑资料
        # self.client.find_element_by_link_text('编辑资料').click()
        # self.client.find_element_by_name('name').send_keys('约翰')
        # self.client.find_element_by_name('location').send_keys('美国')
        # self.client.find_element_by_name('about_me').send_keys('简简单单简简单单')
        # self.client.find_element_by_name('submit').click()
        # self.assertTrue('约翰' in self.client.page_source)
        # self.assertTrue('美国' in self.client.page_source)
        # self.assertTrue('简简单单简简单单' in self.client.page_source)


if __name__ == '__main__':
    unittest.main()
