#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 23:15
# @Author  : willis
# @Site    : 
# @File    : models.py
# @Software: PyCharm

from datetime import datetime
import hashlib

from flask import current_app, request, url_for

from wtforms import ValidationError

from flask_login import UserMixin, AnonymousUserMixin

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from markdown import markdown
import bleach

from . import db, login_manager


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=True, index=True)   # 这里default书上默认False
    permissions = db.Column(db.Integer)

    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def update_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(role_name=r).first()
            if role is None:
                role = Role(role_name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.role_name == default_role)
            db.session.add(role)
        db.session.commit()

    # 关于权限的一些操作

    def reset_permissions(self):
        self.permissions = 0

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.role_name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # 用户资料
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    avatar_hash = db.Column(db.String(32))

    # 虚拟用户
    is_faker = db.Column(db.Boolean, default=False)

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    # 继承一下父类的init
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # 初始化用户角色
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(role_name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        # 初始化gravatar_hash
        if self.email is not None and self.avatar_hash is None:
            self.gravatar_hash()
        # 关注自己
        self.follow(self)

    # 如果库里有一些用户没有关注自己，该方法可以操作
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    # 返回 所有关注的post
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ---- token ----

    def generate_token(self, token_name='default', expiration=3600, **kwargs):
        # token_name 用于识别token的用途，防止串用, 自带id
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        data = {'token_name': token_name, 'user_id': self.id}
        data.update(kwargs)
        return s.dumps(data).decode('utf-8')

    @staticmethod
    def loads_token(token):
        # 解token，并验证user_id和token_name，否则返回None
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
            if data.get('user_id'):
                return data
        except:
            return None

    def change_password(self, old_password, new_password):
        if not self.verify_password(old_password):
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def confirm(self, token):
        data = self.loads_token(token)
        if data is None or data.get('token_name') != 'confirm'\
                or data.get('user_id') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    @staticmethod
    def forgot_password_reset(token, new_password):
        data = User.loads_token(token)
        if data is None\
                or data.get('token_name') != 'forgot_password'\
                or data.get('user_id') is None:
            return False
        user = User.query.get(data.get('user_id'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def change_email(self, token):
        data = self.loads_token(token)
        if data is None\
                or data.get('token_name') != 'change_email'\
                or data.get('user_id') != self.id\
                or data.get('new_email') is None\
                or self.query.filter_by(email=data.get('new_email')).first() is not None:
            return False
        self.email = data.get('new_email')
        db.session.add(self)
        return True

    # 权限验证

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    # 刷新用户最后访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    # gravatar头像

    def gravatar_hash(self):
        # 刷新self.avatar_hash 并返回md5hash
        md5hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        self.avatar_hash = md5hash
        return md5hash

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        md5hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{md5hash}?s={size}&d={default}&r={rating}'.\
            format(url=url, md5hash=md5hash, size=size, default=default, rating=rating)

    # 关注

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    # api auth验证
    @staticmethod
    def verify_auth_token(token):
        data = User.loads_token(token)
        if not data or data.get('token_name') != 'auth':
            return None
        return User.query.get(data.get('user_id'))

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'followed_posts_url': url_for('api.get_user_followed_posts', id=self.id),
            'post_count': self.posts.count()
        }
        return json_user

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):

    def can(self, perm):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


# 加载用户的回调函数 见示例8.8
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    is_faker = db.Column(db.Boolean, default=False)

    @staticmethod
    def on_change_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'url',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)

db.event.listen(Post.body, 'set', Post.on_change_body)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id),
            'post_url': url_for('api.get_post', id=self.post_id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)
