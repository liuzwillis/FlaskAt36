#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 23:04
# @Author  : willis
# @Site    : 
# @File    : errors.py
# @Software: PyCharm

from flask import render_template, request, jsonify
from . import main


@main.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.best == 'application/json':
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403


@main.app_errorhandler(404)
def page_not_found(e):
    # 原来的accept中，若含有*/*,会接受所有形式，改进了一下，如果最期望接受json，则转到json形式
    # if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
    if request.accept_mimetypes.best == 'application/json':
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(405)
def internal_server_error(e):
    if request.accept_mimetypes.best == 'application/json':
        response = jsonify({'error': 'method not allowed'})
        response.status_code = 405
        return response
    return render_template('405.html'), 405


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.best == 'application/json':
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500
