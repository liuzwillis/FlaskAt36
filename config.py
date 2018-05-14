#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 22:11
# @Author  : willis
# @Site    : 
# @File    : config.py
# @Software: PyCharm

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string 123'

    # 每次请求结束后将会自动提交数据库中的变动
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # 如果设置成 True，SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存，不必要可以禁用它。
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 生产环境中启用 缓慢查询记录功能（ch16）
    SQLALCHEMY_RECORD_QUERIES = True
    FLASKY_SLOW_DB_QUERY_TIME = 0.5

    # email 配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.163.com'
    MAIL_PORT = os.environ.get('MAIL_PORT') or 25
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    WEB_NAME = '长颈瓶'
    POST_NAME = '帖子'
    POSTS_PER_PAGE = 20
    FOLLOW_PER_PAGE = 20
    COMMENTS_PER_PAGE = 20

    FLASKY_MAIL_SUBJECT_PREFIX = '[{}]'.format(WEB_NAME)
    # 发件人的格式，可以写成tuple，flask_mail会识别
    FLASKY_MAIL_SENDER = ('{}管理员'.format(WEB_NAME), os.environ.get('MAIL_USERNAME'))
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    # 虚拟用户的密码
    FAKER_PASSWORD = os.environ.get('FAKER_PASSWORD') or 'password'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    # 设置调试模式
    DEBUG = True
    # sql路径
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or\
                              'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or\
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or\
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # 把错误通过邮件发送给管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
