#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/2 002 16:00
# @Author  : willis
# @Site    : 
# @File    : fake.py
# @Software: PyCharm

from random import randint
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
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count-1)).first()
        p = Post(body=fake.text(),
                 timestamp=fake.past_date(),
                 author=u,
                 is_faker=True)
        db.session.add(p)
    db.session.commit()

