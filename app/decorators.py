#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/1 001 1:00
# @Author  : willis
# @Site    : 
# @File    : decorators.py
# @Software: PyCharm

from functools import wraps

from flask import abort
from flask_login import current_user

from .models import Permission


# 检查权限
def permission_required(permission):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function

    return decorator


# 检查是否管理员权限
# 这里再仔细看一下
def admin_required(f):
    return permission_required(Permission.ADMIN)(f)
