from flask import flash, render_template, send_from_directory, current_app, redirect, url_for, request, make_response, jsonify
from flask import get_flashed_messages
from flask_login import current_user, login_user, logout_user, login_required
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

# ------------from current app-------------
from app import db, avatars
from app.models import User
from app.forms import LoginForm, RegistrationForm

from flask import Blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)


# @auth_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data, nickname=form.username.data, email=form.email.data, 
#             name_zh=form.name_zh.data, name_en=form.name_en.data, 
#             chronicle=form.chronicle.data, category=form.category.data)
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Request admitted! Please login', 'success')
#         return redirect(url_for('auth.login'))
#     return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))