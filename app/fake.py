#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/2 002 16:00
# @Author  : willis
# @Site    : 
# @File    : fake.py
# @Software: PyCharm

import random

from faker import Faker

from flask import current_app

from sqlalchemy.exc import IntegrityError

from .import db
from .models import User, Post


def users(count=100):
    fake = Faker(locale='zh-cn')
    i = 0
    while i < count:
        u = User(email=fake.safe_email(),
                 username=fake.user_name(),
                 password=current_app.config['FAKER_PASSWORD'],
                 confirmed=True,
                 name=fake.name(),
                 location=fake.city(),
                 about_me=fake.text(30),
                 member_since=fake.past_date(),
                 is_faker=True)
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def posts(count=100):
    fake = Faker(locale='zh-cn')
    # 只为虚拟用户添加虚拟post
    fake_users = User.query.filter_by(is_faker=True).all()
    for i in range(count):
        u = random.choice(fake_users)
        p = Post(body=fake.text(),
                 timestamp=fake.past_date(),
                 author=u,
                 is_faker=True)
        db.session.add(p)
    db.session.commit()


def delete_users():
    db.session.query(User).filter(User.is_faker == True).delete()
    db.session.commit()


def delete_posts():
    db.session.query(Post).filter(Post.is_faker == True).delete()
    # db.session.query(Post).filter(Post.author.in_(User.query.filter_by(is_faker=True))).delete()
    db.session.commit()