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

    SECRET_KEY = os.environ.get('SECRET_KEY')

    # 每次请求结束后将会自动提交数据库中的变动
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # 如果设置成 True，SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存，不必要可以禁用它。
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # email 配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.163.com'
    MAIL_PORT = os.environ.get('MAIL_PORT') or 25
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    # 发件人的格式，可以写成tuple，flask_mail会识别
    FLASKY_MAIL_SENDER = ('Flasky Admin', os.environ.get('MAIL_USERNAME'))
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

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


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or\
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
