import os, json
import mistune
from PIL import Image
from datetime import datetime

from flask import flash, current_app, redirect, url_for, request
from flask import get_flashed_messages, render_template
from flask_login import current_user, login_required
from flask_simplemde import SimpleMDE
from flask_dropzone import random_filename
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from babel import Locale

# ------------from current app-------------
from app import app, db
from app.models import User, News, History
from app.forms import AddNewsForm, AddEventForm
# though here AddNewsForm is imported, it has not been used
# for the complexity of updating pics and texts at the same time, which may not be supported by Flask-WTF?

from flask import Blueprint
news_bp = Blueprint('news', __name__)

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

def grab_markdown(text):
    content = markdown(text)

    label = re.findall('<h2>.*?</h2>|<h3>.*?</h3>', content)

    sub = [None]*len(label)
    level = [None]*len(label)

    for i in range(len(label)):
        sub[i] = re.search('(?<=<h\d>).*?(?=</h\d>)', label[i]).group()
        level[i] = label[i][2]  

    count = 0

    def convert(matchobj):
        joinlist = [matchobj.group(0)[:3], ' id="toc-', str(count), '">']
        return ''.join(joinlist)

    toc = []
    while (count < len(label)):
        c = int(level[count])
        p = 2
        if count > 0:
            p = int(level[count-1])

        if c > p:
            toc.append('<ul class="toc">\n')
        if c < p:
            toc.append('</ul>\n')
        toc.append('<li class="toc"><a href="#toc-%d">%s</a></li>\n' % (count, sub[count]))
        content = re.sub('<h2>|<h3>', convert, content, 1)
        count += 1

    if re.search('(?<=<h1>).*?(?=</h1>)', content):
        title = re.search('(?<=<h1>).*?(?=</h1>)', content).group()
    else:
        title = 'Default'
    if re.search('(?<=\[tag:).*?(?=\])', content):
        category = re.search('(?<=\[tag:).*?(?=\])', content).group()
    else:
        category = 'Inbox'
    # clean redundant markdowns
    html = re.sub('<h1>.*?</h1>', '', content, 0)
    html = re.sub('\[tag\:.*?\]', '', html, 0)
    menu = (''.join(toc))
    return title, html, menu, category


@news_bp.route('/')
def news():
    page = request.args.get('page', 1, type=int)
    newss = News.query.order_by(News.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    # can also define 'pagination' then pass items attribute like posts=pagination.items, much more clear
    next_url = url_for('.news', page=newss.next_num) \
        if newss.has_next else None
    prev_url = url_for('.news', page=newss.prev_num) \
        if newss.has_prev else None

    events = History.query.all()
    history = []
    for event in events:
        valuelist = [event.id, event.name, event.location, event.startdate.strftime('%Y,%m,%d'), event.enddate.strftime('%Y,%m,%d')]
        history.append(valuelist)
    return render_template('news/news.html', title='News', history=history, newss=newss.items, next_url=next_url, prev_url=prev_url)
# this is only one static page, at least for now. We will add more loading stuff to it.

"""
@news_bp.route('/news/upload_img', methods=['GET', 'POST'])
@login_required
def upload_img():
    if request.method == 'POST':
        for f in request.files.getlist('file'):
            f.save(os.path.join(app.config['NEWS_IMG_PATH'], f.filename))
    return render_template('news/news.html')
"""

@news_bp.route('/story/<int:news_id>', methods=['GET', 'POST'])
def show_news(news_id):
    news = News.query.get_or_404(news_id)
    imgs = str(news.img_path).split("*")
    notes = str(news.img_note).split("*")
    sizes = str(news.img_size).split("*")
    html_cn = parse_markdown(news.text_cn)
    html_en = parse_markdown(news.text_en)
    return render_template('news/story.html', news=news, imgs=imgs, notes=notes, sizes=sizes, html_cn=html_cn, html_en=html_en)


@news_bp.route('/whatsnew', methods=['GET', 'POST'])
@login_required
def whatsnew():
    form = AddNewsForm()
    if request.method == 'POST':
        for f in request.files.getlist('file'):
            f.save(os.path.join(app.config['NEWS_IMG_PATH'], f.filename))
    return render_template('news/add_news.html', form=form)


@news_bp.route('/pubnews', methods=['GET', 'POST'])
def pubnews():
    img_path = []
    img_note = []
    img_size = []

    form = AddNewsForm()
    if request.method == 'POST':
        project_prefix = datetime.now().strftime('%C%m%d%H%M')
        for f in request.files.getlist('file'):
            if f:
                f_name = project_prefix + '_' + random_filename(f.filename) # this function will remain the original extension, don't bother using os.path
                img_path.append(f_name)
                f.save(os.path.join(app.config['NEWS_IMG_PATH'], f_name))
                image = Image.open(os.path.join(app.config['NEWS_IMG_PATH'], f_name))
                img_size.append(str(image.size[0]) + 'x' + str(image.size[1]))
                sizo = 300;
                image.thumbnail((sizo,sizo))
                image.save(os.path.join(app.config['NEWS_IMG_PATH'], '_' + f_name))
        for n in request.form.getlist('note'):
            img_note.append(n)
        if img_path:
            img_jumbo = img_path[0]
        else:
            img_jumbo = ''

        title_cn = form.title_cn.data
        title_en = form.title_en.data
        text_cn = form.text_cn.data
        text_en = form.text_en.data
        category = form.category.data
        date = form.date.data
        location = form.location.data
        news = News(title_cn=title_cn, title_en=title_en, text_cn=text_cn, text_en=text_en, category=category, date=date, author=current_user,
            img_jumbo=img_jumbo, img_path="*".join(img_path), img_note="*".join(img_note), img_size="*".join(img_size))
        db.session.add(news)
        db.session.commit()
        flash('Newsletter released!', 'success')
    return redirect(url_for('.news'))

@news_bp.route('/whatsplan', methods=['GET', 'POST'])
@login_required
def whatsplan():
    """ # absolete
    def rectify(datetime):
        splitdate = datetime.strftime('%Y-%m-%d').split('-')
        month = int(splitdate[1]) - 1
        recdate = '-'.join([splitdate[0],str(month),splitdate[2]])
        return recdate
    """
    form = AddEventForm()
    if form.validate_on_submit():
        history = History(name=form.name.data, location=form.location.data, 
            startdate=form.startdate.data, enddate=form.enddate.data)
        db.session.add(history)
        db.session.commit()
        flash('Circled on calendar', 'success')
        return redirect(url_for('.whatsplan'))
    return render_template('news/add_event.html', title='Add Schedule', form=form)


@news_bp.route('/upload_img', methods=['GET', 'POST'])
def upload_img():
    if request.method == 'POST':
        file = request.files['file']
        f_name = random_filename(file.filename)
        file.save(os.path.join(app.config['NEWS_IMG_PATH'], f_name))
    return json.dumps({'filename':f_name})


@news_bp.route('/story/<int:news_id>/delete', methods=['POST'])
@login_required
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    filelist = str(news.img_path).split("*") if news.img_path else []
    for file in filelist:
        os.remove(os.path.join(app.config['NEWS_IMG_PATH'], file))
        os.remove(os.path.join(app.config['NEWS_IMG_PATH'], '_' + file))
    news_del = news.id
    db.session.delete(news)
    db.session.commit()
    flash('Newsletter deleted.', 'danger')
    return redirect(url_for('.news'))


@news_bp.route('/story/<int:news_id>/jumbo', methods=['GET', 'POST'])
@login_required
def jumbo_news(news_id):
    news = News.query.get_or_404(news_id)
    news.jumbotron = not news.jumbotron
    db.session.commit()
    return redirect(url_for('.show_news', news_id=news.id))


@news_bp.route('/story/<int:news_id>/edit', methods=['GET', 'POST'])
def edit_news(news_id):
    news = News.query.get_or_404(news_id)
    form = AddNewsForm(category=news.category)
    if form.validate_on_submit():
        news.title_cn = form.title_cn.data
        news.title_en = form.title_en.data
        news.text_cn = form.text_cn.data
        news.text_en = form.text_en.data
        news.date = form.date.data
        news.location = form.location.data
        db.session.commit()
        flash('Revised', 'success')
        return redirect(url_for('.show_news', news_id=news.id))
    elif request.method == 'GET':
        form.title_cn.data = news.title_cn
        form.title_en.data = news.title_en
        form.text_cn.data = news.text_cn
        form.text_en.data = news.text_en
        form.date.data = news.date
        form.location.data = news.location
    return render_template('news/edit_news.html', title='Edit Story', form=form, news=news)
