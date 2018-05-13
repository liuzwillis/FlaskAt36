#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/13 013 13:09
# @Author  : willis
# @Site    : 
# @File    : decorators.py
# @Software: PyCharm

from functools import wraps
from flask import g
from .errors import forbidden


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return f(*args, **kwargs)
        return decorated_function
    return decorator
