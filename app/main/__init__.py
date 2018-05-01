#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 22:51
# @Author  : willis
# @Site    : 
# @File    : __init__.py
# @Software: PyCharm

from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission


# 将Permission类加入模板上下文
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
