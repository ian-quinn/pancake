import os, re, json
import mistune
from PIL import Image
from datetime import datetime
import time #for the project process calculation
import sys

from flask import flash, render_template, current_app, redirect, url_for, request, send_from_directory
from flask import get_flashed_messages, g
from flask_login import current_user, login_required
from flask_dropzone import random_filename
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from babel import Locale

# ------------from current app-------------
from app import app, db
from app.models import Project, User, Document
from app.forms import AddProjectForm

from flask import Blueprint
proj_bp = Blueprint('proj', __name__)

# markdown parsing settings --------------------------------------------------------------------
# markdown = mistune.Markdown(escape=False, hard_wrap=False)
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

def get_locale():
    if current_user.is_authenticated and current_user.locale is not None:
        return current_user.locale

    locale = request.cookies.get('locale')
    if locale is not None:
        return locale
    return request.accept_languages.best_match(current_app.config['LOCALES'])


#------------------------BLOG PAGE -------------------------------

@proj_bp.route('/list', methods=['GET', 'POST'])
def project():
    projects = Project.query.order_by(Project.startdate.desc()).all()
    return render_template('proj/project_list.html', title='Project', projects=projects)

@proj_bp.route('/dashboard', methods=['GET', 'POST'])
def project_dashboard():
    projects = Project.query.order_by(Project.startdate.desc()).all()
    return render_template('proj/project_dashboard.html', title='Project', projects=projects)

# custom filter for outdated projects
@app.template_filter('getstatus')
def getstatus(id):
    project = Project.query.filter_by(id=int(id)).first_or_404()
    date = datetime.now()
    if project.enddate:
        deadline = project.enddate
    else:
        deadline = date
    if date >= deadline:
        return True
    else:
        return False

@proj_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    filelist = str(project.filename).split("*") if project.filename else []
    for file in filelist:
        os.remove(os.path.join(app.config['PROJECT_PATH'], file))
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'danger')
    return redirect(url_for('.project'))

@proj_bp.route('/<int:project_id>', methods=['GET', 'POST'])
def show_project(project_id):
    project = Project.query.get_or_404(project_id)
    documents = Document.query.filter_by(project_id=project_id).all()
    filename = str(project.filename).split("*") if project.filename else []
    filenote = str(project.filenote).split("*") if project.filenote else []
    checklist = project.members.split("*") if project.members else []

    # render the member list. not the same with the check list
    memberlist = []
    if project.members:
        for identity in project.members.split("*"):
            memberlist.append(User.query.get(int(identity)))

    now = datetime.now()
    if project.startdate and project.enddate:
        if (now < project.enddate):
            if now < project.startdate:
                process = 0
            else:
                process = round((now - project.startdate) * 100 / (project.enddate - project.startdate))
        else:
            process = 100
    elif project.startdate and not project.enddate:
        process = 80
    elif project.enddate and not project.startdate:
        if (now < project.enddate):
            process = 50
        else:
            process = 100
    else:
        process = 0
    """
    documentlist = []
    posterlist = []
    if len(filename) > 0:
        for name in filename:
            note = filenote[filename.index(name)]
            if name.lower().endswith(('.png', '.jpg', '.jpeg')):
                posterlist.append((name, note))
            else:
                note = note + os.path.splitext(name)[1]
                documentlist.append((name, note))
                """
    posterlist = list(zip(filename, filenote))

    title_cn = project.title_cn
    title_en = project.title_en
    html_cn = parse_markdown(project.brief_cn)
    html_en = parse_markdown(project.brief_en)

    # recruit members to this project, only form, no conflict
    if request.method == 'POST':
        if str(current_user.id) not in checklist:
            checklist.append(str(current_user.id))
            project.members = "*".join(checklist)
            db.session.commit()
            flash('Enrolled!', 'success')
        else:
            flash('Enrolled already.', 'warning')
        return redirect(url_for('.show_project', project_id=project.id))
    
    return render_template('proj/project_item.html', project=project, html_cn=html_cn, html_en=html_en, 
        documentlist=documents, posterlist=posterlist, process=process, memberlist=memberlist)

@proj_bp.route('/attachment:<int:document_id>/block', methods=['GET', 'POST'])
@login_required
def block(document_id):
    document = Document.query.get_or_404(document_id)
    document.islocked = not document.islocked
    db.session.commit()
    return redirect(url_for('.show_project', project_id=document.project_id))

@proj_bp.route('/attachment:<int:document_id>/download', methods=['GET', 'POST'])
def download(document_id):
    document = Document.query.get_or_404(document_id)
    uploads = os.path.join(current_app.root_path, app.config['PROJECT_PATH'])
    extension = os.path.splitext(document.filename)[1]
    return send_from_directory(directory=uploads, filename=document.filename, as_attachment=True, attachment_filename=document.filenote + extension)

@proj_bp.route('/addproject', methods=['GET', 'POST'])
@login_required
def addproject():
    form = AddProjectForm()
    return render_template('proj/add_project.html', form=form)

@proj_bp.route('/kickoff', methods=['GET', 'POST'])
@login_required
def kickoff():
    posters = []
    poster_notes = []
    documents = []
    document_notes = []
    form = AddProjectForm()
    if request.method == 'POST':
        uploadlist_file = request.files.getlist('file')
        uploadlist_note = request.form.getlist('note')
        # uploadlist_note will be like ['', ''] when inputs are left blank
        project_prefix = datetime.now().strftime('%m%d%H%M')
        for i in range(len(uploadlist_file)):
            if uploadlist_file[i]:
                f_name = project_prefix + '_' + random_filename(uploadlist_file[i].filename)[-12:] # this function will remain the original extension, don't bother using os.path
                if f_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    posters.append(f_name)
                    poster_notes.append(uploadlist_note[i])
                else:
                    documents.append(f_name)
                    if uploadlist_note[i]:
                        document_notes.append(uploadlist_note[i])
                    else:
                        document_notes.append(os.path.splitext(uploadlist_file[i].filename)[0])
                        # set default filenote same as the filename
                uploadlist_file[i].save(os.path.join(app.config['PROJECT_PATH'], f_name))

        title_cn = form.title_cn.data
        title_en = form.title_en.data
        brief_cn = form.brief_cn.data if form.brief_cn.data else '暂无此项目说明'
        brief_en = form.brief_en.data if form.brief_en.data else 'No information available'
        startdate = form.startdate.data
        enddate = form.enddate.data
        isthesis = bool(form.isthesis.data)
        banner = posters[0] if posters else ""
        project = Project(title_cn=title_cn, title_en=title_en, brief_cn=brief_cn, brief_en=brief_en, 
            startdate=startdate, enddate=enddate, filename="*".join(posters), filenote="*".join(poster_notes), banner=banner, isthesis=isthesis)
        # filename & filenote are misleading but the model of database is set, no way to change it.
        db.session.add(project)
        db.session.flush()

        for i in range(len(documents)):
            document = Document(filename=documents[i], filenote=document_notes[i], project=project)
            db.session.add(document)
        db.session.commit()
        flash('New project launched!', 'success')
    return redirect(url_for('.project'))

@proj_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    form = AddProjectForm()
    project = Project.query.get_or_404(project_id)
    if form.validate_on_submit():
        project.title_cn = form.title_cn.data
        project.title_en = form.title_en.data
        project.brief_cn = form.brief_cn.data
        project.brief_en = form.brief_en.data
        project.startdate = form.startdate.data
        project.enddate = form.enddate.data
        project.isthesis = form.isthesis.data
        db.session.commit()
        flash('Revised', 'success')
        return redirect(url_for('.show_project', project_id=project.id))
    elif request.method == 'GET':
        form.title_cn.data = project.title_cn
        form.title_en.data = project.title_en
        form.brief_cn.data = project.brief_cn
        form.brief_en.data = project.brief_en
        form.startdate.data = project.startdate
        form.enddate.data = project.enddate
        form.isthesis.data = project.isthesis
    return render_template('proj/edit_project.html', title='Edit Project', form=form, project=project)
