#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/24 024 10:40
# @Author  : willis
# @Site    : 
# @File    : __init__.py
# @Software: PyCharm

from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views
