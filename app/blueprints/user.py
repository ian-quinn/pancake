import os, re, json, sys
import mistune
from PIL import Image

from flask import flash, render_template, send_from_directory, current_app, redirect, url_for, request
from flask import get_flashed_messages, g
from flask_login import current_user, login_user, logout_user, login_required
from flask_simplemde import SimpleMDE
from flask_dropzone import random_filename
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from babel import Locale

# ------------from current app-------------
from app import app, db, avatars
from app.models import User, Post
from app.forms import EditProfileForm, CropAvatarForm, UploadAvatarForm, JumboAvatarForm
from app.forms import EditPasswordForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email import send_password_reset_email

from flask import Blueprint
user_bp = Blueprint('user', __name__)

def get_locale():
    if current_user.is_authenticated and current_user.locale is not None:
        return current_user.locale

    locale = request.cookies.get('locale')
    if locale is not None:
        return locale
    return request.accept_languages.best_match(current_app.config['LOCALES'])


@user_bp.route('/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user/user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)

@user_bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username), 'warning')
        return redirect(url_for('blog.blog'))
    if user == current_user:
        flash('You cannnot follow yourself', 'warning')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}'.format(username), 'warning')
    return redirect(url_for('.user', username=username))

@user_bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username), 'warning')
        return redirect(url_for('blog.blog'))
    if user == current_user:
        flash('You cannot unfollow yourself', 'warning')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username), 'warning')
    return redirect(url_for('.user', username=username))

@user_bp.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def set_profile():
    form = EditProfileForm(current_user.username, current_user.email, category=current_user.category)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_zh = form.about_zh.data
        current_user.about_en = form.about_en.data
        current_user.email = form.email.data
        current_user.name_zh = form.name_zh.data
        current_user.name_en = form.name_en.data
        current_user.chronicle = form.chronicle.data
        current_user.category = form.category.data
        current_user.googlescholar = form.googlescholar.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('.set_profile'))
    form.username.data = current_user.username
    form.about_zh.data = current_user.about_zh
    form.about_en.data = current_user.about_en
    form.email.data = current_user.email
    form.name_zh.data = current_user.name_zh
    form.name_en.data = current_user.name_en
    form.chronicle.data = current_user.chronicle
    form.category.data = current_user.category
    form.googlescholar.data = current_user.googlescholar
    # i dont know but the selectfield likely has to be initiated at the loading stage.
    return render_template('user/set_profile.html', title='Edit Profile', form=form)


@user_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(app.config['AVATARS_SAVE_PATH'], filename)


@user_bp.route('/settings/photo', methods=['GET', 'POST'])
@login_required
def set_photo():
    form = JumboAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = current_user.username + '_jumbo.png'
        image.save(os.path.join(app.config['AVATARS_SAVE_PATH'], filename))
        current_user.avatar_jumbo = filename
        db.session.commit()
        flash('Image uploaded', 'success')
    return  render_template('user/set_photo.html', title='Edit photo', form=form)


@user_bp.route('/settings/avatar', methods=['GET', 'POST'])
@login_required
def set_avatar():
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('user/set_avatar.html', title='Edit Avatar', upload_form=upload_form, crop_form=crop_form)


@user_bp.route('/settings/avatar/crop', methods=['POST'])
@login_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        previous_avatar_m = current_user.avatar_m
        previous_avatar_l = current_user.avatar_l
        current_user.avatar_m = filenames[1]
        current_user.avatar_l = filenames[2]
        rawpicture = current_user.avatar_raw
        current_user.avatar_raw = ''
        db.session.commit()
        os.remove(os.path.join(app.config['AVATARS_SAVE_PATH'], filenames[0]))
        if rawpicture:
            os.remove(os.path.join(app.config['AVATARS_SAVE_PATH'], rawpicture))
        if previous_avatar_m:
            os.remove(os.path.join(app.config['AVATARS_SAVE_PATH'], previous_avatar_m))
        if previous_avatar_l:
            os.remove(os.path.join(app.config['AVATARS_SAVE_PATH'], previous_avatar_l))
        flash('Image updated', 'success')
    return  redirect(url_for('.set_avatar'))


@user_bp.route('/settings/avatar/upload', methods=['POST'])
@login_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        current_user.avatar_raw = avatars.save_avatar(image)
        db.session.commit()
        flash('Image uploaded', 'success')
    return  redirect(url_for('.set_avatar'))


@user_bp.route('/settings/password', methods=['GET', 'POST'])
@login_required
def set_password():
    form = EditPasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.password.data)
            db.session.commit()
            flash('Password updated.', 'success')
        else:
            flash('Old password is incorrect.', 'danger')
    return  render_template('user/set_password.html', title='Edit Password', form=form)

@user_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'success')
        return redirect(url_for('auth.login'))
    return render_template('user/reset_password_request.html', title='Reset Password', form=form)

@user_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('user/reset_password.html', form=form)

