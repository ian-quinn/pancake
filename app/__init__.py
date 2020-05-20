from flask import Flask
from flask import request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_avatars import Avatars
from flask_simplemde import SimpleMDE
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from flask_dropzone import Dropzone
from flask_babel import Babel
from flask_whooshee import Whooshee
from flask_mail import Mail
from elasticsearch import Elasticsearch

import logging
import os, sys
from logging.handlers import SMTPHandler, RotatingFileHandler


# application factory functions:
app = Flask(__name__)
app.config.from_object(Config)

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.163.com',
    MAIL_PORT = 994,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = 'bsimtongji@163.com',
    MAIL_PASSWORD = 'infwhrsynwpsu441',
))


db = SQLAlchemy(app)
migrate = Migrate(app, db, compare_type=True)
login = LoginManager(app)
login.login_view = 'login'

avatars = Avatars(app)
simplemde = SimpleMDE(app)
moment = Moment(app)
dropzone = Dropzone(app)
babel = Babel(app)
whooshee = Whooshee(app)
mail = Mail(app)

csrf = CSRFProtect(app)

@babel.localeselector
def get_locale():
	if current_user.is_authenticated and current_user.locale is not None:
		return current_user.locale

	locale = request.cookies.get('locale')
	if locale is not None:
		return locale
	return request.accept_languages.best_match(current_app.config['LOCALES'])

app.jinja_env.globals.update(get_locale=get_locale)


from app.blueprints.errors import errors_bp
app.register_blueprint(errors_bp, url_prefix='/errors')
from app.blueprints.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
from app.blueprints.blog import blog_bp
app.register_blueprint(blog_bp, url_prefix='/blog')
from app.blueprints.user import user_bp
app.register_blueprint(user_bp, url_prefix='/user')
from app.blueprints.news import news_bp
app.register_blueprint(news_bp, url_prefix='/news')
from app.blueprints.proj import proj_bp
app.register_blueprint(proj_bp, url_prefix='/project')
from app.blueprints.offset import offset_bp
app.register_blueprint(offset_bp, url_prefix='/offset')
# reconstruct these registers when all blueprints are done
# use fatory function create_app

from app import routes, models


if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        print('error with Post.search', file=sys.stderr)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Logger standing by')