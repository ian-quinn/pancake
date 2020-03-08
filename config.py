import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    	'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    AVATARS_SAVE_PATH = os.path.join(basedir,'app/static/avatars')
    AVATARS_SIZE_TUPLE = (20, 50, 100)
    PUBS_UPLOAD_PATH = os.path.join(basedir,'app/static/publications')
    IMG_PATH = os.path.join(basedir,'app/static/img')
    POST_IMG_PATH = os.path.join(basedir,'app/static/postemp')
    NEWS_IMG_PATH = os.path.join(basedir,'app/static/newstemp')
    PROJECT_PATH = os.path.join(basedir,'app/static/projtemp')
    BOOKSHELF_PATH = os.path.join(basedir,'app/static/bookshelf')
    
    LOCALES = ['en', 'zh']
    BABEL_DEFAULT_LOCALE = LOCALES[1]

    POSTS_PER_PAGE = 12
    COMMENT_PER_PAGE = 20

    # for simpleMDE initialization
    SIMPLEMDE_JS_IIFE = True
    SIMPLEMDE_USE_CDN = True

    DROPZONE_MAX_FILE_SIZE = 10
    DROPZONE_MAX_FILE = 3
    DROPZONE_ALLOWED_FILE_CUSTOM = True
    DROPZONE_ALLOWED_FILE_TYPE = '.pdf, image/*, .docx'
    DROPZONE_ENABLE_CSRF = False
    DROPZONE_UPLOAD_ON_CLICK=True
    DROPZONE_UPLOAD_ACTION='handle_upload'  # URL or endpoint
    DROPZONE_UPLOAD_BTN_ID='submit'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('ADMINS')


