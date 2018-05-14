#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/23 023 23:01
# @Author  : willis
# @Site    : 
# @File    : views.py
# @Software: PyCharm

from flask import render_template, session, redirect,\
    url_for, current_app, request, flash, abort, make_response

from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import User, Role, Post, Permission, Comment
from ..decorators import admin_required, permission_required


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           pagination=pagination, show_followed=show_followed)


@main.route('/user/<username>')
def user(username):
    user_ = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user_.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user_, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('资料已更新。')
        return redirect(url_for('main.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('该用户的资料已经更新.')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post_ = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post_,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('你的评论已经发布')
        return redirect(url_for('main.post', post_id=post_.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post_.comments.count() - 1) // current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post_.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post_], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post_ = Post.query.get_or_404(post_id)
    if current_user != post_.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post_.body = form.body.data
        db.session.add(post_)
        flash('{}已经更新'.format(current_app.config['POST_NAME']))
        return redirect(url_for('main.post', post_id=post_.id))
    form.body.data = post_.body
    return render_template('edit_post.html', form=form)


# -----------------关注------------------------

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('没有找到该用户')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('您已经关注了该用户')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('成功关注 %s.' % username)
    return redirect(url_for('main.user', username=username))


@main.route('/unfollow/<username>')
@login_required
# 取关也需要FOLLOW权限，也就是说，如果之前关注了某人，
# 后来管理员下了你的FOLLOW权限，那么你再也不能取关了，是这样吗？
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('没有找到该用户')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('您没有关注该用户')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('取关成功： %s' % username)
    return redirect(url_for('main.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page,
                                         per_page=current_app.config['FOLLOW_PER_PAGE'],
                                         error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='的粉丝',
                           endpoint='main.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效的用户')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page,
                                        per_page=current_app.config['FOLLOW_PER_PAGE'],
                                        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='的关注',
                           endpoint='main.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


# ------------管理评论-------------

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('main.moderate',
                            page=request.args.get('page', 1, type=int)))