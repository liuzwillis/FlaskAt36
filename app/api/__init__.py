#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/13 013 10:14
# @Author  : willis
# @Site    : 
# @File    : __init__.py
# @Software: PyCharm


from flask import Blueprint

api = Blueprint('api', __name__)

from . import authentication, posts, users, comments, errors
