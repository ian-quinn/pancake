from flask import render_template
from app import db

from flask import Blueprint
errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(400)
def bad_request(error):
	return render_template('errors/400.html'), 400

@errors_bp.app_errorhandler(404)
def forbidden(error):
	return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(404)
def not_found_error(error):
	return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(413)
def request_entity_too_large(error):
	return render_template('errors/413.html'), 413

@errors_bp.app_errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('errors/500.html'), 500