#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 23:01
# @Author  : willis
# @Site    : 
# @File    : views.py
# @Software: PyCharm

from flask import render_template, session, redirect, url_for, current_app, request, flash

from flask_login import login_user

from . import main
from .forms import NameForm
from .. import db
from ..models import User
from ..email import send_email


@main.route('/')
def index():
    return render_template('index.html')


