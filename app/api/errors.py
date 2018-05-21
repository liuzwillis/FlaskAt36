#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/13 013 10:37
# @Author  : willis
# @Site    : 
# @File    : errors.py
# @Software: PyCharm

from flask import jsonify
from app.exceptions import ValidationError
from . import api


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


# def method_not_allowed(message):
#     response = jsonify({'error': 'method_not_allowed', 'message': message})
#     response.status_code = 405
#     return response


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])


# @api.errorhandler(405)
# def method_error(e):
#     return method_not_allowed(e.args[0])
