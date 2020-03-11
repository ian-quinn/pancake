import os, re, json
import mistune
from PIL import Image

from flask import flash, render_template, current_app, redirect, url_for, request, send_from_directory, send_file
from flask import get_flashed_messages, g
from flask_login import current_user, login_user, logout_user, login_required
from flask_simplemde import SimpleMDE
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from babel import Locale
from pypinyin import lazy_pinyin

# ------------from current app-------------
from app import app, db, avatars
from app.models import User, Post, Comment, Category
from app.forms import PostForm, CommentForm, UserCommentForm

from flask import Blueprint
blog_bp = Blueprint('blog', __name__)

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
        toc.append('<li class="toc "><a href="#toc-%d" class="list-group-item">%s</a></li>\n' % (count, sub[count]))
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

@blog_bp.route('/', methods=['GET', 'POST'])
def blog():
    """
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!', 'success')
        return redirect(url_for('blog'))
    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    # can also define 'pagination' then pass items attribute like posts=pagination.items, much more clear
    next_url = url_for('.blog', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('.blog', page=posts.prev_num) \
        if posts.has_prev else None

    categories = Category.query.order_by(Category.id.desc()).all()

    return render_template('blog/blog.html', title='Blog', posts=posts.items, next_url=next_url, prev_url=prev_url, categories=categories)
    # posts=posts.items is for pass the 'items' attribute from pagination class 'posts' and overwrite it.
'''
@blog_bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('blog/blog.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)
'''

@blog_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    initvalue_cn = post.text_cn.replace('\r','\\r').replace('\n','\\n') # !!!here contaminate the markdown file, need revise
    initvalue_en = post.text_en.replace('\r','\\r').replace('\n','\\n') # !!!here contaminate the markdown file, need revise
    return render_template('blog/edit_post.html', initvalue_en=initvalue_en, initvalue_cn=initvalue_cn, post=post) # here insert the default post id

@blog_bp.route('/newpost', methods=['GET', 'POST'])
@login_required
def newpost():
    if request.method == "POST":
        text_cn = request.json['text_cn']
        text_en = request.json['text_en']
        title_cn, html_cn, menu_cn, tag_cn = grab_markdown(text_cn)
        title_en, html_en, menu_en, tag_en = grab_markdown(text_en)
        authors = current_user.id
        markdown_title = title_en if title_en else title_cn
        sourcemd = ''.join(lazy_pinyin(markdown_title))[0:61] + '.md'

        if tag_cn:
        	tag = tag_cn
        else:
        	if tag_en:
        		tag = tag_en
        	else:
        		tag = 'Inbox'

        if Category.query.filter_by(name=tag).first() == None:
            category = Category(name=tag)
            db.session.add(category)
            db.session.flush()
            category_id = category.id
            db.session.commit()
        else:
            category_id = Category.query.filter_by(name=tag).first().id

        post = Post(text_cn=text_cn, text_en=text_en, title_cn=title_cn, title_en=title_en, author=current_user, 
            authors=authors, category_id=category_id, sourcemd=sourcemd)
        db.session.add(post)
        db.session.flush()
        target = post.id
        db.session.commit()

        f = open(os.path.join(app.config['POST_IMG_PATH'], sourcemd), 'w+', encoding = 'utf-8')
        f.write(text_cn)
        f.write('\n-------------------------------------------------------\n')
        f.write(text_en)
        f.close()

        flash('Thanks for your participation!', 'success')
        return redirect(url_for('.show_post', post_id=target))
    return render_template('blog/add_post.html')
    

@blog_bp.route('/copost', methods=['GET', 'POST'])
@login_required
def copost():
    if request.method == "POST":
        target = request.json['post_id']
        text_cn = request.json['text_cn']
        text_en = request.json['text_en']
        if target:
            post = Post.query.get_or_404(target)
            checklist = post.authors.split("*")
            if str(current_user.id) not in checklist:
                checklist.append(str(current_user.id))
                post.authors = "*".join(checklist)
            post.text_cn = text_cn
            post.text_en = text_en
            post.title_cn = grab_markdown(text_cn)[0]
            post.title_en = grab_markdown(text_en)[0]
            tag_cn = grab_markdown(text_cn)[3]
            tag_en = grab_markdown(text_en)[3]

            if tag_cn:
            	tag = tag_cn
            else:
            	if tag_en:
            		tag = tag_en
            	else:
            		tag = 'Inbox'

            if Category.query.filter_by(name=tag).first() == None:
                category = Category(name=tag)
                db.session.add(category)
                db.session.flush()
                post.category_id = category.id
                db.session.commit()
            else:
            	post.category_id = Category.query.filter_by(name=tag).first().id

            f = open(os.path.join(app.config['POST_IMG_PATH'], sourcemd), 'w+', encoding = 'utf-8')
            f.write(text_cn)
            f.write('\n-------------------------------------------------------\n')
            f.write(text_en)
            f.close()

            db.session.commit()
        flash('Thanks for your participation!', 'success')
    return redirect(url_for('.show_post', post_id=target))

@blog_bp.route('/postimg', methods=['GET', 'POST'])
def postimg():
    urllist = []
    if request.method == 'POST':
        for f in request.files.getlist('image'):
            filename = datetime.now().strftime('%C%m%d_%H%M%S' + os.path.splitext(f.filename)[1])
            f.save(os.path.join(app.config['POST_IMG_PATH'], filename))
            urllist.append(os.path.join("/static/postemp/", filename))
    key = ['url']
    data = json.dumps(dict(zip(key, urllist)))
    return data


@blog_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    authorlist = []
    for identity in post.authors.split("*"):
        authorlist.append(User.query.get(int(identity)))

    page = request.args.get('page', 1, type=int)
    if get_locale() == 'en':
        title, html, menu, category = grab_markdown(post.text_en)
    else:
        title, html, menu, category = grab_markdown(post.text_cn)
    pagination = Comment.query.with_parent(post).filter_by(reviewed=True).order_by(
        Comment.timestamp.asc()).paginate(page, app.config['COMMENT_PER_PAGE'], False)
    comments = pagination.items
    authors = post.authors
    next_url = url_for('.show_post', post_id=post_id, page=pagination.next_num) \
        if pagination.has_next else None
    prev_url = url_for('.show_post', post_id=post_id, page=pagination.prev_num) \
        if pagination.has_prev else None
  
    if current_user.is_authenticated:
        form = UserCommentForm()
        form.author.data = current_user.username
        form.email.data = 'DEFAULT@bsim.tongji.edu.cn'
        reviewed = True
        if current_user.username == post.author.username:
            from_author = True
        else:
            from_author = False
    else:
        form = CommentForm()
        reviewed = True
        from_author = False

    if form.validate_on_submit():
        comment = Comment(author=form.author.data, email=form.email.data, 
            body=form.body.data, from_author=from_author, post=post, reviewed=reviewed)
        replied_id = request.args.get('reply')
        if replied_id:
            replied_comment = Comment.query.get_or_404(replied_id)
            comment.replied = replied_comment
        db.session.add(comment)
        db.session.commit()
        flash('Published!', 'success')
        return redirect(url_for('.show_post', post_id=post_id)+ '#commentop')
    return render_template('blog/post.html', post=post, html=html, menu=menu, title=title, form=form, comments=comments, 
        pagination=pagination, next_url=next_url, prev_url=prev_url, authorlist=authorlist)

@blog_bp.route('/post/<int:post_id>/download', methods=['GET', 'POST'])
def download(post_id):
    post = Post.query.get_or_404(post_id)
    fumblepath = os.path.join(current_app.root_path, app.config['POST_IMG_PATH'])
    title = post.title_cn if post.title_cn else post.title_en
    return send_from_directory(directory=fumblepath, filename=post.sourcemd, as_attachment=True, attachment_filename="%s.md" % title)

@blog_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    post_del = post.id
    markdown_path = os.path.join(app.config['POST_IMG_PATH'], post.sourcemd)
    if os.path.exists(markdown_path):
        os.remove(markdown_path)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'danger')
    return redirect(url_for('.blog'))

@blog_bp.route('/post/<int:post_id>/block', methods=['GET', 'POST'])
@login_required
def block_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.islocked = not post.islocked
    db.session.commit()
    return redirect(url_for('.show_post', post_id=post.id))

@blog_bp.route('/post/<int:post_id>/mute', methods=['GET', 'POST'])
@login_required
def mute_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.can_comment = not post.can_comment
    db.session.commit()
    return redirect(url_for('.show_post', post_id=post.id))

@blog_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if not comment.post.can_comment:
        flash('Comment disabled.', 'warning')
        return redirect(url_for('.show_post', post_id=comment.post.id))
    return redirect(
        url_for('.show_post', post_id=comment.post_id, reply=comment_id, author=comment.author) + '#commentop')


@blog_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment_del = comment.post.id
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'danger')
    return redirect(url_for('.show_post', post_id=comment_del) + '#commentop')
    # work around, need to refer to redirect_back function like blueblog

@blog_bp.route('/category/<int:category_id>')
def show_category(category_id):
    category = Category.query.get_or_404(category_id)
    categories = Category.query.all()

    posts = Post.query.with_parent(category).order_by(Post.timestamp.desc()).all()

    return render_template('blog/category.html', category=category, posts=posts, categories=categories)
