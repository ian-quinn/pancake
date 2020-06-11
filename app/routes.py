import os, re, json
import mistune
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime
import time #for the project process calculation

from flask import flash, render_template, send_from_directory, current_app, redirect, url_for, request, make_response, jsonify
from flask import get_flashed_messages, g
from flask_login import current_user, login_user, logout_user, login_required
from flask_simplemde import SimpleMDE
from flask_dropzone import random_filename
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename

from pypinyin import lazy_pinyin
from babel import Locale

# ------------from current app-------------
from app import app, db, avatars
from app.models import User, Paper, Post, Comment, News, File, Project, History, Category, Photo
from app.forms import LoginForm, RegistrationForm, EditProfileForm, AddPubsForm, EditPubsForm, PostForm, CommentForm, UserCommentForm, AddProjectForm
from app.forms import CropAvatarForm, UploadAvatarForm, JumboAvatarForm, EditPasswordForm, AddNewsForm, AddEventForm, SearchForm


###### Markdown configurations #######
class MyCustomRenderer(mistune.Renderer):
    def image(self, src, title, alt_text):
        if alt_text == 'img-responsive':
            return "<img src='%s' class='img-responsive'>" % (src)
        else:
            return "<img src='%s' title='%s' class='img-box'>" % (src, alt_text)
renderer = MyCustomRenderer()
markdown = mistune.Markdown(renderer=renderer, escape=False, hard_wrap=False)

def parse_markdown(text):
    content = markdown(text)
    return content


@app.route('/')
@app.route('/index')
def index():
    papers = Paper.query.filter_by(category = 1).order_by(Paper.date.desc()).limit(5).all()
    newss = News.query.order_by(News.date.desc()).limit(5).all()
    return render_template('index.html', title='Home', papers=papers, newss=newss)
# @login_required

def get_locale():
    if current_user.is_authenticated and current_user.locale is not None:
        return current_user.locale

    locale = request.cookies.get('locale')
    if locale is not None:
        return locale
    return request.accept_languages.best_match(current_app.config['LOCALES'])

#---------------Markdown presetting complete---------------------------------------

@app.route('/set_locale/<locale>')
def set_locale(locale):
    if locale not in current_app.config['LOCALES']:
        return jsonify(message='Invalid locale.'), 404
    response = make_response(redirect(request.referrer))
    if current_user.is_authenticated:
        current_user.locale = locale
        db.session.commit()
    else:
        response.set_cookie('locale', locale, max_age= 60*60*24*30)
    return response


"""--------------abandoned for the time being---------------------
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_zh = form.about_zh.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_zh.data = current_user.about_zh
    return render_template('edit_profile.html', title='Edit Profile', form=form)
    """

# ----------------------------------PUBLICATION--------------------------

@app.route('/pubs', methods=['GET', 'POST'])
def pubs():
    papers = Paper.query.order_by(Paper.date.desc()).all()
    form = AddPubsForm()
    # if request.method == 'POST' and 'file' in request.files:
        # f = request.files.get('ile')
        # filename = random_filename(f.filename)
        # f.save(os.path.join(app.config['PUBS_UPLOAD_PATH'], filename))
    if form.validate_on_submit():
        # never alter the format when storing the data
        title = form.title.data
        author = str.title(form.author.data)
        coauthor = str.title(form.coauthor.data)
        citation = form.citation.data
        issci = form.is_sci.data
        isei = form.is_ei.data
        if form.file.data:
            filename = re.sub('\s', '_', str.capitalize(title[0:32]), 0) + '.pdf'
            f = form.file.data
            if os.path.splitext(f.filename)[1] != '.pdf':
                flash('PDF only!', 'danger')
                return redirect(url_for('pubs'))
            f.save(os.path.join(app.config['PUBS_UPLOAD_PATH'], filename))
        else:
            filename = ''
        paper = Paper(title=title, author=author, coauthor=coauthor, filename=filename, 
            journal=form.journal.data, date=form.date.data, category=form.category.data,
            abstract=form.abstract.data, citation=citation, issci=issci, isei=isei)
        db.session.add(paper)
        db.session.commit()
        flash('Paper cached!', 'success')
        return redirect(url_for('pubs'))
    return render_template('pubs.html', title='Publication', form=form, papers=papers)


@app.route('/pubs/<cate>', methods=['GET', 'POST'])
def filt_pubs(cate):
    form = AddPubsForm()
    papers = Paper.query.filter_by(category = cate).all()
    return render_template('pubs.html', title=cate, form=form, papers=papers)


@app.route('/pubs/<int:paper_id>/delete', methods=['POST'])
@login_required
def delete_pubs(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    if paper.filename:
        file_path = os.path.join(app.config['PUBS_UPLOAD_PATH'], paper.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(paper)
    db.session.commit()
    flash('Paper deleted.', 'danger')
    return redirect(url_for('pubs'))

@app.route('/pubs/<int:paper_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_pubs(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    form = EditPubsForm()
    if form.validate_on_submit():
        paper.title = form.title.data
        paper.author = str.title(form.author.data)
        paper.coauthor = str.title(form.coauthor.data)
        paper.journal = form.journal.data
        paper.date = form.date.data
        paper.category = form.category.data
        paper.abstract = form.abstract.data
        paper.citation = form.citation.data
        paper.issci = form.is_sci.data
        paper.isei = form.is_ei.data
        paper.islocked = form.is_locked.data
        db.session.commit()
        flash('Changes have been saved.', 'success')
        return redirect(url_for('pubs'))
    form.title.data = paper.title
    form.author.data = paper.author
    form.coauthor.data = paper.coauthor
    form.journal.data = paper.journal
    form.date.data = paper.date
    form.category.data = paper.category
    form.abstract.data = paper.abstract
    form.citation.data = paper.citation
    form.is_sci.data = paper.issci
    form.is_ei.data = paper.isei
    return render_template('edit_pubs.html', form=form, paper=paper)


@app.route('/pubs/<int:paper_id>/download', methods=['GET'])
def download_pubs(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    uploads = os.path.join(current_app.root_path, app.config['PUBS_UPLOAD_PATH'])
    return send_from_directory(directory=uploads, filename=paper.filename, as_attachment=True, attachment_filename="%s.pdf" % paper.title)


@app.route('/search', methods=['GET', 'POST'])
def search():
    q = request.args.get('q', '')
    if q == '':
        return redirect(url_for('pubs'))
    papers = Paper.query.whooshee_search(q).all()

    f = open(os.path.join(app.config['PUBS_UPLOAD_PATH'], 'Citation.txt'), 'w+', encoding = 'utf-8')
    for paper in papers:
        if paper.citation:
            f.write(paper.citation)
            f.write('\n')
        else:
            f.write(paper.author + ', ' + paper.coauthor + '. ' + paper.title + '. ' + paper.journal + ', ' 
                + paper.date.strftime('%Y-%m') + '. (Not formatted)\n')
    f.close()
    #for hit in papers:
    #    print(hit.highlights("title"), file=sys.stderr)
    return render_template('search.html', q=q, papers=papers)


#----------------dash line-------------------------------------------------

"""
@app.route('/user/settings/avatar')
@login_required
def set_figure():
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('edit_avatar.html', upload_form=upload_form, crop_form=crop_form)

@app.route('/avatars/upload', methods=['POST'])
@login_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = avatars.save_avatar(image)
        current_user.avatar_raw = filename
        db.session.commit()
        flash('Image uploaded', 'success')
    return  redirect(url_for('edit_avatar'))

@app.route('/avatars/jumbo', methods=['POST'])
@login_required
def jumbo_avatar():
    form = JumboAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = current_user.username + '_jumbo'
        image.save(os.path.join(app.config['AVATARS_SAVE_PATH'], filename))
        current_user.avatar_jumbo = filename
        db.session.commit()
        flash('Image uploaded', 'success')
    return  redirect(url_for('edit_avatar'))

@app.route('/avatars/crop', methods=['POST'])
@login_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        current_user.avatar_s = filenames[0]
        current_user.avatar_m = filenames[1]
        db.session.commit()
        flash('Image updated', 'success')
    return  redirect(url_for('edit_avatar'))
"""

@app.route('/people', methods=['GET', 'POST'])
def people():
    users = User.query.order_by(User.username.desc()).all()
    return render_template('people.html', title='People', users=users)
    
@app.route('/humanresourcemachine', methods=['GET', 'POST'])
@login_required
def humanresourcemachine():
    users = User.query.order_by(User.chronicle.desc()).all()
    return render_template('HRM.html', title='People', users=users)

@app.route('/humanresourcemachine/<int:user_id>/delete', methods=['POST'])
@login_required
def fire(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Fired.', 'danger')
    return redirect(url_for('humanresourcemachine'))

@app.route('/humanresourcemachine/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def hire(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileForm(user.username, user.email, category=user.category)
    if form.validate_on_submit():
        user.username = form.username.data
        user.about_zh = form.about_zh.data
        user.about_en = form.about_en.data
        user.email = form.email.data
        user.chronicle = form.chronicle.data
        user.category = form.category.data
        user.googlescholar = form.googlescholar.data
        user.name_zh = form.name_zh.data
        user.name_en = form.name_en.data
        db.session.commit()
        flash('Your changes have been saved.', 'success')
        return redirect(url_for('humanresourcemachine'))
    form.username.data = user.username
    form.about_zh.data = user.about_zh
    form.about_en.data = user.about_en
    form.email.data = user.email
    form.name_zh.data = user.name_zh
    form.name_en.data = user.name_en
    form.chronicle.data = user.chronicle
    form.googlescholar.data = user.googlescholar
    form.category.data = user.category
    return render_template('HRM_edit.html', title='Edit Profile', form=form)
    

# ---------------------------------------------------------------------------------

@app.route('/bookshelf')
def bookshelf():
    #list = os.listdir(app.config['BOOKSHELF_PATH'])
    files = File.query.all()
    document = File.query.filter_by(category=1).order_by(File.name.desc()).all()
    package = File.query.filter_by(category=2).order_by(File.name.desc()).all()
    video = File.query.filter_by(category=3).order_by(File.name.desc()).all()
    miscs = File.query.filter_by(category=0).order_by(File.name.desc()).all()
    return render_template('bookshelf.html', files=files, document=document, package=package, video=video, miscs=miscs)


@app.route('/bookshelf/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    file_path = os.path.join(app.config['BOOKSHELF_PATH'], file.link)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(file)
    db.session.commit()
    flash('File deleted.', 'danger')
    return redirect(url_for('bookshelf'))


@app.route('/bookshelf/<int:file_id>/download', methods=['GET', 'POST'])
def download(file_id):
    file = File.query.get_or_404(file_id)
    uploads = os.path.join(current_app.root_path, app.config['BOOKSHELF_PATH'])
    return send_from_directory(directory=uploads, filename=file.link, as_attachment=True, attachment_filename="%s" % file.name)


@app.route('/bookshelf/<int:file_id>/block', methods=['GET', 'POST'])
@login_required
def block(file_id):
    file = File.query.get_or_404(file_id)
    file.islocked = not file.islocked
    db.session.commit()
    return redirect(url_for('bookshelf'))


@app.route('/bookshelf/uploadfile', methods=['GET', 'POST'])
@login_required
def uploadfile():
    if request.method == 'POST':
        for f in request.files.getlist('file'):
            name = f.filename
            # Skim out duplicated files
            if File.query.filter_by(name=name).first() is None:
                
                # Security stuff
                surname = os.path.splitext(name)[0]
                bookend = os.path.splitext(name)[1]
                tempname = ''.join(lazy_pinyin(name))
                link = secure_filename(tempname)
                
                if bookend in ['.doc', '.docx', '.ppt', '.pptx', '.xml', '.xmls', '.pdf', '.txt', '.md', '.csv']:
                    category = 1
                elif bookend in ['.zip', '.rar', '.7z', '.iso']:
                    category = 2
                elif bookend in ['.mp4', '.mov', '.rmvb', '.mkv', '.mp3', '.avi', '.flv']:
                    category = 3
                elif ['.jpg', '.png', '.gif', '.jpeg', '.tif', '.tiff']:
                    category = 4
                else:
                    category = 0

                path = os.path.join(app.config['BOOKSHELF_PATH'], link)
                f.save(path)
                size = os.stat(path).st_size
                if size > 1000:
                    if size > 1000000:
                        size = str(round(size/1024/1024, 2)) + ' MB'
                    else:
                        size = str(int(size/1024)) + ' KB'
                else:
                    size = str(size) + ' B'

                file = File(name=name, link=link, size=size, bookend=bookend, category=category)
                db.session.add(file)
                db.session.commit()
    return ('', 204)


# ---------------------------------------------------------------------------------

@app.route('/album')
def album():
    page = request.args.get('page', 1, type=int)
    photos = Photo.query.order_by(Photo.timestamp.desc()).paginate(page, 30 , False)
    # can also define 'pagination' then pass items attribute like posts=pagination.items, much more clear
    next_url = url_for('album', page=photos.next_num) \
        if photos.has_next else None
    prev_url = url_for('album', page=photos.prev_num) \
        if photos.has_prev else None
    return render_template('album.html', photos=photos.items, next_url=next_url, prev_url=prev_url) # .items is crucial


@app.route('/album/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_path = os.path.join(app.config['ALBUM_PATH'], photo.link)
    if os.path.exists(photo_path):
        os.remove(photo_path)
    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted.', 'danger')
    return redirect(url_for('album'))

@app.route('/album/uploadfile', methods=['GET', 'POST'])
@login_required
def uploadphoto():
    if request.method == 'POST':
        for f in request.files.getlist('file'):
            prefix = datetime.now().strftime('%C%m%d')
            # Security stuff
            link = prefix + '_' + random_filename(f.filename)
            path = os.path.join(app.config['ALBUM_PATH'], link)
            f.save(path)
            image = Image.open(path)
            size = str(image.size[0]) + 'x' + str(image.size[1])
            image.thumbnail((300,300))
            image.save(os.path.join(app.config['ALBUM_PATH'], 'thumbnail/' + link))

            photo = Photo(link=link, size=size)
            db.session.add(photo)
            db.session.commit()
    return ('', 204)


# --------------------------------------------------------------------------------------


########################################################
########################################################
########################################################
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}


@app.route('/markdown')
def tips_md():
    return render_template('markdown.html', title='Tips')

@app.template_filter('dateformat')
def dateformat(value, format='%Y-%m-%d'):
    return value.strftime(format)

@app.template_filter('stripout')
def stripout(text):
    html = markdown(text)
    plaintext = ''.join(BeautifulSoup(html).findAll(text=True))
    return plaintext

@app.template_filter('mdparse')
def mdparse(text):
    html = markdown(text)
    return html