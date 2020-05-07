from flask_wtf import FlaskForm
from datetime import datetime
from flask import request
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField, HiddenField, DateField, SelectField, IntegerField, DateTimeField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, NumberRange, Optional, URL
from app.models import User

####################################################################################
#--------------------------------authentication forms-------------------------------
class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(message="What's the username?")])
	password = PasswordField('Password', validators=[DataRequired(message="Password?")])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
	username = StringField('ID Number', validators=[DataRequired(message="Your student ID")])
	name_zh = StringField('Chinese name', validators=[DataRequired()])
	name_en = StringField('English name', validators=[DataRequired()])
	chronicle = IntegerField('Enrollment year', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	category = SelectField('Category', choices=[(1,'Tutor'), (2,'Doctoral candidate'), (3,'Postgraduate'), (4,'Alumni'), (5,'Friend')], default=1, coerce=int)
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField(
		'Confirm password', validators=[DataRequired(), EqualTo('password',message="Not exactly the same. Type again")])
	submit = SubmitField('Sign Up')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError('Username already exists.')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('Email address already exists.')

	def validate_chronicle(self, chronicle):
		if chronicle.data < 2006 or chronicle.data > 2025:
			raise ValidationError('Enrollment year format: XXXX ')


####################################################################################
#----------------------------------main route forms---------------------------------

class AddNewsForm(FlaskForm):
	title_cn = StringField('TitleCN', validators=[DataRequired()])
	title_en = StringField('TitleEN', validators=[DataRequired()])
	text_cn = TextAreaField('DescriptionCN', validators=[DataRequired()])
	text_en = TextAreaField('DescriptionEN', validators=[DataRequired()])
	category = SelectField('Category', choices=[(1,'Academic'), (2,'Amusement'), (3,'Appointment')], default=1, coerce=int)
	date = DateTimeField('Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
	location = StringField('Location')
	submit = SubmitField('Publish')
"""
	def validate_date(form, field):
		try:
			datetime.strptime(field.data, '%Y-%m-%d %H:%M')
		except Exception:
			raise ValidationError('Wrong Input Format!')
			"""

class AddEventForm(FlaskForm):
	name = StringField('Name', validators=[DataRequired(message="What's your plan?")])
	location = StringField('Location')
	startdate = DateTimeField('Start', format='%Y-%m-%d', validators=[DataRequired()])
	enddate = DateTimeField('End', format='%Y-%m-%d', validators=[DataRequired()])
	submit = SubmitField('Pin')

	def validate_enddate(self, enddate):
		if enddate.data < self.startdate.data:
			raise ValidationError("Time arrow cannot be reversed.")

class AddProjectForm(FlaskForm):
	title_cn = StringField('TitleCN', validators=[DataRequired()])
	title_en = StringField('TitleEN', validators=[DataRequired()])
	brief_cn = TextAreaField('BriefingCN')
	brief_en = TextAreaField('BriefingEN')
	startdate = DateTimeField('Start', format='%Y-%m-%d', validators=[Optional()])
	enddate = DateTimeField('End', format='%Y-%m-%d', validators=[Optional()])
	category = SelectField('Category', choices=[(1,'重点专项'), (2,'模拟咨询'), (3,'课题企划')], default=1, coerce=int)
	submit = SubmitField('Done!')

class AddPubsForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired(message="Title must be specified")])
	author = StringField('Author', validators=[DataRequired(message="The author is needed for retrieving")])
	coauthor = StringField('Co-Author')
	journal = StringField('Journal')
	date = DateField('Publish date', format='%Y-%m')
	category = SelectField('Category', choices=[(1,'英文期刊'), (2,'中文期刊'), (3,'会议论文'), (4,'学位论文')], default=1, coerce=int)
	file = FileField('Choose PDF file...', validators=[FileAllowed(['pdf', 'PDF'], message='PDF only!')])
	abstract = TextAreaField('Briefing')
	citation = TextAreaField('Citation')
	is_sci = BooleanField('SCI?')
	is_ei = BooleanField('EI?')
	submit = SubmitField('Go!')

	# why did i add this line?
	#def validate_date(self, chronicle):
	#	if chronicle.data < 2006 or chronicle.data > 2025:
	#		raise ValidationError('Enrollment year format: XXXX ')

class EditPubsForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired(message="Title must be specified")])
	author = StringField('Author', validators=[DataRequired(message="The author is needed for retrieving")])
	coauthor = StringField('Co-Author')
	journal = StringField('Journal', validators=[DataRequired(message="Journal info is necessary")])
	date = DateField('Publish date', format='%Y-%m')
	category = SelectField('Category', choices=[(1,'英文期刊'), (2,'中文期刊'), (3,'会议论文'), (4,'学位论文')], default=1, coerce=int)
	abstract = TextAreaField('Briefing')
	citation = TextAreaField('Citation')
	is_sci = BooleanField('SCI?')
	is_ei = BooleanField('EI?')
	submit = SubmitField('Submit')

class PostForm(FlaskForm):
	post = TextAreaField('Say something', validators=[DataRequired()])
	submit = SubmitField('Submit')

class CommentForm(FlaskForm):
    author = StringField('Name', validators=[DataRequired(message="Your appellation?"), Length(max=32)])
    email = StringField('Email', validators=[DataRequired(message="The email will now be shown"), Email(), Length(max=256)])
    body = TextAreaField('Comment', validators=[DataRequired(message="Say something")])
    submit = SubmitField()

class UserCommentForm(CommentForm):
    author = HiddenField()
    email = HiddenField()

######################################################################################
#-----------------------------------user forms ---------------------------------------

class EditProfileForm(FlaskForm):
	about_zh = TextAreaField('关于', validators=[Length(min=0, max=10000)])
	about_en = TextAreaField('About me', validators=[Length(min=0, max=10000)])
	username = StringField('Username', validators=[DataRequired(), Length(1, 16)])
	email = StringField('New Email', validators=[DataRequired(), Length(1, 32), Email()])
	category = SelectField('Category', choices=[(1,'Tutor'), (2,'Doctoral candidate'), (3,'Postgraduate'), (4,'Alumni'), (5,'Friend')], coerce=int)
	chronicle = IntegerField('Enrollment year', validators=[DataRequired()])
	name_zh = StringField('姓名')
	name_en = StringField('Name')
	googlescholar = StringField('Google Scholar Profile', validators=[URL(message='URL not valid'), Optional()])
	submit = SubmitField('Submit')

	def __init__(self, original_username, original_email, *args, **kwargs):
		super(EditProfileForm, self).__init__(*args, **kwargs)
		self.original_username = original_username
		self.original_email = original_email

	def validate_username(self, username):
		if username.data != self.original_username:
			user = User.query.filter_by(username=self.username.data).first()
			if user is not None:
				raise ValidationError('Please use a different username.')

	def validate_email(self, email):
		if email.data != self.original_email:
			if User.query.filter_by(email=email.data.lower()).first():
				raise ValidationError('The email is already in use.')

class UploadAvatarForm(FlaskForm):
	image = FileField('Upload (<=3M)', validators=[FileRequired(), FileAllowed(['jpg','png'], 'Wrong file type')])
	submit = SubmitField()

class JumboAvatarForm(FlaskForm):
	image = FileField('Upload (<=3M)', validators=[FileRequired(), FileAllowed(['jpg','png'], 'Only .jpg and .png formats are supported')])
	submit = SubmitField()

class CropAvatarForm(FlaskForm):
	x = HiddenField()
	y = HiddenField()
	w = HiddenField()
	h = HiddenField()
	submit = SubmitField('Crop and Update')

class EditPasswordForm(FlaskForm):
	old_password = PasswordField('Password', validators=[DataRequired()])
	password = PasswordField('New Password', validators=[DataRequired()])
	password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Not exactly the same. Type again")])
	submit = SubmitField()

class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Reset Password')

######################################################################################
#------------------------------search engine forms -----------------------------------

class SearchForm(FlaskForm):
	q = StringField('Searchingngngn', validators=[DataRequired()])

	def __init__(self, *args, **kwargs):
		if 'formdata' not in kwargs:
			kwargs['formdata'] = request.args
		if 'csrf_enabled' not in kwargs:
			kwargs['csrf_enabled'] = False
		super(SearchForm, self).__init__(*args, **kwargs)


