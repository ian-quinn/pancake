import mistune
import re
import jwt
from time import time
from datetime import datetime
from app import db, login, whooshee, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from flask_avatars import Identicon



markdown = mistune.Markdown(escape=False, hard_wrap=False)


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)
# whether to use real time rendering or cache html in the database?
# for now we are not caching htmls for saving the storage
"""
class MyCustomRenderer(mistune.Renderer):
    def image(self, src, title, alt_text):
        if alt_text == 'img-responsive':
            return "<img src='%s' class='img-responsive'>" % (src)
        else:
            return "<img src='%s' title='%s' class='img-box'>" % (src, alt_text)


renderer = MyCustomRenderer()
markdown = mistune.Markdown(renderer=renderer)
"""
# search service supporting paper skimming
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True)
    nickname = db.Column(db.String(32), unique=True)
    name_zh = db.Column(db.String(16))
    name_en = db.Column(db.String(16))
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    category = db.Column(db.Integer)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    newss = db.relationship('News', backref='author', lazy='dynamic')
    about_zh = db.Column(db.Text)
    about_en = db.Column(db.Text)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_raw = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    avatar_jumbo = db.Column(db.String(64))
    chronicle = db.Column(db.Integer)
    locale = db.Column(db.String(16))
    googlescholar = db.Column(db.String(128))
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.generate_avatar()

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
    	self.password_hash = generate_password_hash(password)

    def check_password(self, password):
    	return check_password_hash(self.password_hash, password)

    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

########### news and calendar support #####################
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    date = db.Column(db.DateTime)
    location = db.Column(db.String(64))
    category = db.Column(db.Integer)
    title_cn = db.Column(db.String(64))
    title_en = db.Column(db.String(64))
    text_cn = db.Column(db.Text)
    text_en = db.Column(db.Text)
    img_path = db.Column(db.String(256))
    img_jumbo = db.Column(db.String(64))
    img_note = db.Column(db.String(256))
    img_size = db.Column(db.String(16))
    jumbotron = db.Column(db.Boolean, default=False)
'''
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return '<News {}>'.format(self.body)
        '''


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    startdate = db.Column(db.DateTime)
    enddate = db.Column(db.DateTime)

############### huge bulk of post & comments and tags ###################
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    text_cn = db.Column(db.Text)
    text_en = db.Column(db.Text)
    title_cn = db.Column(db.String(64))
    title_en = db.Column(db.String(64))
    can_comment = db.Column(db.Boolean, default=True)
    islocked = db.Column(db.Boolean, default=False)
    authors = db.Column(db.String(64))
    sourcemd = db.Column(db.String(64))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    category = db.relationship('Category', back_populates='posts')

    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        #self.grab_markdown()

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    """
    def grab_markdown(self):
        content = markdown(self.body)

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
            self.title = re.search('(?<=<h1>).*?(?=</h1>)', content).group()
        self.html = re.sub('<h1>.*?</h1>', '', content, 0)
        self.menu = (''.join(toc))

        db.session.commit()
    """

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(32))
    email = db.Column(db.String(256))
    body = db.Column(db.Text)
    from_author = db.Column(db.Boolean, default=False)
    reviewed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    post = db.relationship('Post', back_populates='comments')
    replies = db.relationship('Comment', back_populates='replied', cascade='all, delete-orphan')
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])
    # Same with:
    # replies = db.relationship('Comment', backref=db.backref('replied', remote_side=[id]),
    # cascade='all,delete-orphan')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)

    posts = db.relationship('Post', back_populates='category')

    def delete(self):
        default_category = Category.query.get(1)
        posts = self.posts[:]
        for post in posts:
            post.category = default_category
        db.session.delete(self)
        db.session.commit()

    #def count(self):
    #    return 


#############################  publication  ###################################

@whooshee.register_model('title', 'author', 'coauthor', 'abstract', 'date', 'journal')
class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    author = db.Column(db.String(32))
    coauthor = db.Column(db.String(128))
    journal = db.Column(db.String(128))
    date = db.Column(db.DateTime)
    category = db.Column(db.Integer)
    abstract = db.Column(db.Text)
    citation = db.Column(db.String(1024))
    filename = db.Column(db.String(64))
    issci = db.Column(db.Boolean, default=False)
    isei = db.Column(db.Boolean, default=False)


###############  for caching project  #####################
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_cn = db.Column(db.String(128))
    title_en = db.Column(db.String(128))
    startdate = db.Column(db.DateTime)
    enddate = db.Column(db.DateTime)
    brief_cn = db.Column(db.Text)
    brief_en = db.Column(db.Text)
    filename = db.Column(db.String(256))
    filenote = db.Column(db.String(256))
    banner = db.Column(db.String(64))
    isthesis = db.Column(db.Boolean, default=False)
    category = db.Column(db.Integer)
    members = db.Column(db.String(64))
    # new line here to identify document references
    documents = db.relationship('Document', backref='project', lazy='dynamic')

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256))
    filenote = db.Column(db.String(256))
    islocked = db.Column(db.Boolean, default=False)
    # new lines here to link projects
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

############# bookshelf supporting  ########################
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(64))
    size = db.Column(db.String(64))
    bookend = db.Column(db.String(8))
    category = db.Column(db.Integer)
    link = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    islocked = db.Column(db.Boolean, default=False)

############# album supporting  ########################
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    link = db.Column(db.String(64))
    size = db.Column(db.String(16))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))






