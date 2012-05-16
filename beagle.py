import uuid
import datetime
import settings
from flask import Flask, request, redirect, url_for, session, flash, render_template
from flaskext.oauth import OAuth
from flaskext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from functools import wraps
from wtforms import Form, TextField, IntegerField, SelectMultipleField
from sqlalchemy.sql import or_, and_
from dateutil.parser import parse

# initialize the things

app = Flask(__name__)
oauth = OAuth()
app.secret_key = settings.APP_SECRET_KEY
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
db = SQLAlchemy(app)


# base model

game_tags = db.Table('game_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('game_id', db.String(36), db.ForeignKey('game.id'))
)

lead_tags = db.Table('lead_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('lead_id', db.String(36), db.ForeignKey('lead.id'))
)

contact_tags = db.Table('contact_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('contact_id', db.String(36), db.ForeignKey('contact.id'))
)

game_genders = db.Table('game_genders',
    db.Column('gender_id', db.Integer, db.ForeignKey('gender.id')),
    db.Column('game_id', db.String(36), db.ForeignKey('game.id'))
)

game_ages = db.Table('game_ages',
    db.Column('age_id', db.Integer, db.ForeignKey('age.id')),
    db.Column('game_id', db.String(36), db.ForeignKey('game.id'))
)

game_statuses = db.Table('game_statuses',
    db.Column('status_id', db.Integer, db.ForeignKey('status.id')),
    db.Column('game_id', db.String(36), db.ForeignKey('game.id'))
)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(36), primary_key=True)
    fb_id = db.Column(db.String(80))
    name = db.Column(db.String(160))
    email = db.Column(db.String(80))

    def __init__(self, fb_id=fb_id, name=name, email=email, id=None):
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')
        self.fb_id = fb_id
        self.name = name
        self.email = email

class Lead(db.Model):
    __tablename__ = 'lead'
    id = db.Column(db.String(36), primary_key=True)
    developer = db.Column(db.String(80), index=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    website = db.Column(db.String(200), index=True)
    note = db.Column(db.Text)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    tags = db.relationship('Tag', secondary=lead_tags, backref=db.backref('leads', lazy='dynamic'))

    user = db.relationship(User, backref='leads', lazy='joined')

    def __init__(self, developer=developer, website=website, user_id=user_id, note=None, id=None):
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')
        self.developer = developer
        self.website = website
        self.note = note
        self.user_id = user_id

class Contact(db.Model):
    __tablename__ = 'contact'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), index=True)
    email = db.Column(db.String(80), unique=True, index=True)
    phone = db.Column(db.String(80), index=True)
    title = db.Column(db.String(120), index=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    lead_id = db.Column(db.String(36), db.ForeignKey('lead.id'))
    tags = db.relationship('Tag', secondary=contact_tags, backref=db.backref('contacts', lazy='dynamic'))

    lead = db.relationship(Lead, backref='contacts', lazy='joined')

    def __init__(self, lead_id=lead_id, name=name, email=email, phone=phone, title=title, id=None):
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')
        self.lead_id = lead_id
        self.name = name
        self.email = email
        self.title = title
        self.phone = phone

class Game(db.Model):
    __tablename__ = 'game'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), index=True)
    lead_id = db.Column(db.String(36), db.ForeignKey('lead.id'))
    ratings = db.Column(db.Integer)
    dau = db.Column(db.Integer)
    platform = db.Column(db.String(80))
    int_date = db.Column(db.DateTime, index=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    tags = db.relationship('Tag', secondary=game_tags, backref=db.backref('games', lazy='dynamic'))
    ages = db.relationship('Age', secondary=game_ages, backref=db.backref('games', lazy='dynamic'))
    genders = db.relationship('Gender', secondary=game_genders, backref=db.backref('games', lazy='dynamic'))
    statuses = db.relationship('Status', secondary=game_statuses, backref=db.backref('games', lazy='dynamic'))


    lead = db.relationship(Lead, backref='games', lazy='joined')


    def __init__(self, name=name, lead_id=lead_id, ratings=ratings, platform=platform, ages=ages, genders=genders, statuses=statuses, tags=tags,int_date=int_date, dau=None, id=None):
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')
        self.name = name
        self.lead_id = lead_id
        self.ratings = ratings
        self.platform = platform
        self.ages = ages
        self.genders = genders
        self.statuses = statuses
        self.tags = tags
        self.int_date = int_date
        if dau is None:
            self.dau = int(self.ratings * float(settings.RATINGS_MULTIPLIER))

class Age(db.Model):
    __tablename__ = 'age'
    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    name = db.Column(db.String(40), index=True)

    def __init__(self, name):
        self.name = name

class Gender(db.Model):
    __tablename__ = 'gender'
    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    name = db.Column(db.String(40), index=True)

    def __init__(self, name):
        self.name = name

class Status(db.Model):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    name = db.Column(db.String(40), index=True)

    def __init__(self, name):
        self.name = name

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    name = db.Column(db.String(40), index=True)

    def __init__(self, name):
        self.name = name

# Forms

class LeadForm(Form):
    lead_id = TextField('lead_id')
    developer = TextField('developer')
    website = TextField('website')
    note = TextField('note')
    user_id = TextField('user_id')

class GameForm(Form):
    lead_id = TextField('lead_id')
    game_id = TextField('game_id')
    name = TextField('name')
    ratings = IntegerField('ratings')
    ages = SelectMultipleField('ages')
    statuses = SelectMultipleField('statuses')
    genders = SelectMultipleField('genders')
    platform = TextField('platform')
    int_date = TextField('int_date')

class ContactForm(Form):
    lead_id = TextField('lead_id')
    contact_id = TextField('contact_id')
    name = TextField('name')
    email = TextField('email')
    phone = TextField('phone')
    title = TextField('title')

class AttributeForm(Form):
    name = TextField('name')
    id = IntegerField('id')

# oauth settings (this can be pretty easily swapped out for twitter/github/etc.)

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=settings.FACEBOOK_CONSUMER,
    consumer_secret=settings.FACEBOOK_SECRET,
    request_token_params={'scope': 'email'}
)

# cached functions (TODO Caching)
def get_attributes():
    attributes = {'ages': Age.query.all(), 'genders': Gender.query.all(), 'statuses': Status.query.all(), 'tags': Tag.query.all()}
    return attributes

# decorators
def auth_required(role):
    def decorator(f):
        @wraps(f)
        def inner(*a, **kw):
            if not session.get('user'):
                flash(u'<strong>Access denied:</strong> You must be logged in to use this application.', 'alert-error')
                return redirect(url_for('index'))
            else:
                return f(*a, **kw)
        return inner
    return decorator

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

def strip_http(url):
    clean_url = str(url).replace('http://', '').replace('https://', '')
    return clean_url
# views
@app.route("/")
def index():
    if not session.get('user'):
        return render_template('login.html')
    lead_query = Lead.query.order_by(Lead.created.desc()).options(joinedload('user'))
    leads = lead_query.limit(10).all()
    game_query = Game.query.order_by(Game.created.desc()).options(joinedload('lead.user'))
    games = game_query.limit(10).all()
    users = User.query.all()
    return render_template('index.html', leads=leads, games=games, users=users)

@app.route("/search")
@auth_required('user')
def search():
    query = str(request.args['query'])
    lead_query = Lead.query.order_by(Lead.created).options(joinedload('user'))
    leads = lead_query.filter(Lead.developer.ilike("%" + query + "%")).all()
    leads += lead_query.filter(Lead.website.ilike("%" + query + "%")).all()
    unq_leads = dict([(l.id, l) for l in leads])
    leads = unq_leads.values()
    contact_query = Contact.query.order_by(Contact.created).options(joinedload('lead'))
    contacts = contact_query.filter(Contact.email.ilike("%" + query + "%")).all()
    contacts += contact_query.filter(Contact.name.ilike("%" + query + "%")).all()
    contacts += contact_query.filter(Contact.phone.ilike("%" + query + "%")).all()
    contacts += contact_query.filter(Contact.title.ilike("%" + query + "%")).all()
    unq_contacts = dict([(c.id, c) for c in contacts])
    contacts = unq_contacts.values()
    games = Game.query.filter(Game.name.ilike("%" + query + "%")).all()
    return render_template('search.html', leads=leads, games=games, contacts=contacts)


@app.route("/browse")
@auth_required('user')
def browse():
    args = request.args
    games = []
    if request.method == 'GET' and args:
        genders = args.getlist('genders')
        ages = args.getlist('ages')
        statuses = args.getlist('statuses')
        all_sets = []
        if not len(ages) == 0:
            age_ids = []
            for age in ages:
                age_obj = Age.query.filter_by(name=age).first()
                age_ids.append(age_obj.id)
            age_set = Game.query.join('ages').filter(Age.id.in_(age_ids)).distinct().all()
            all_sets.append(set(age_set))
        if not len(genders) == 0:
            gen_ids = []
            for gender in genders:
                gen_obj = Gender.query.filter_by(name=gender).first()
                gen_ids.append(gen_obj.id)
            gen_set = Game.query.join('genders').filter(Gender.id.in_(gen_ids)).distinct().all()
            all_sets.append(set(gen_set))
        if not len(statuses) == 0:
            stat_ids = []
            for status in statuses:
                stat_obj = Status.query.filter_by(name=status).first()
                stat_ids.append(stat_obj.id)
            stat_set = Game.query.join('statuses').filter(Status.id.in_(stat_ids)).distinct().all()
            all_sets.append(set(stat_set))
        result = set.intersection(*all_sets)
        games = result
        return render_template('browse.html', games=games, args=args, attributes=get_attributes())
    return render_template('browse.html', args=args, attributes=get_attributes())

@app.route("/add/lead", methods=['POST'])
@auth_required('user')
def add_lead():
    form = LeadForm(request.form)
    if request.method == 'POST' and form.validate():
        lead = Lead(form.developer.data, strip_http(form.website.data), session['user'])
        try:
            db.session.add(lead)
            db.session.commit()
            app.logger.info("The lead %s was added." % lead.developer)
            flash(u'Your lead was succesfully saved as <strong><a href=\"/lead/%s\">%s</a></strong>. It\'s automatically been assigned to you. Add a game below.' % (lead.id, lead.developer), 'alert-success')
        except:
            flash('Something went wrong! We couldn\'t add your contact!', 'alert-danger')
            return redirect(url_for('add_lead'))
    return redirect('/new/contact/%s' % lead.id)

@app.route("/add/game", methods=['POST'])
@auth_required('user')
def add_game():
    form = GameForm(request.form)
    if request.method == 'POST':
        genders = []
        ages = []
        statuses = []
        tags = []
        for item in form.genders.data:
            gender = Gender.query.filter_by(name=item).first()
            genders.append(gender)
        for item in form.ages.data:
            gender = Age.query.filter_by(name=item).first()
            ages.append(gender)
        for item in form.statuses.data:
            gender = Status.query.filter_by(name=item).first()
            statuses.append(gender)

        date = parse(form.int_date.data)
        game = Game(form.name.data, form.lead_id.data, form.ratings.data, form.platform.data, ages, genders, statuses, tags, date)
        try:
            db.session.add(game)
            db.session.commit()
            app.logger.info("The game %s was added." % game.name)
            flash(u'Your game was succesfully saved as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (game.lead_id, game.name), 'alert-success')
        except Exception as e:
            flash('Something went wrong! We couldn\'t add your game!', 'alert-danger')
            app.logger.error(e)
            return redirect('/lead/%s' % form.lead_id.data)
        return redirect('/lead/%s' % game.lead_id)
    else:
        flash('Something went wrong! We couldn\'t add your game!', 'alert-danger')
        return redirect('/lead/%s' % form.lead_id.data)

@app.route("/add/contact", methods=['POST'])
@auth_required('user')
def add_contact():
    form = ContactForm(request.form)
    if request.method == 'POST' and form.validate():
        contact = Contact(form.lead_id.data, form.name.data, form.email.data, form.phone.data, form.title.data)
        try:
            db.session.add(contact)
            db.session.commit()
            app.logger.info("%s was added to the lead %s" % (contact.name, contact.lead.developer))
            flash(u'Your contact was succesfully added as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (contact.lead_id, contact.name), 'alert-success')
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % form.email.data, 'alert-warning')
            return redirect('/search?query=%s' % form.email.data)
        except Exception as e:
            flash('Something went wrong! We couldn\'t add your contact!', 'alert-danger')
            app.logger.error(e)
        if request.args.get('state') == 'exist':
            return redirect('/lead/%s' % contact.lead_id)
        return redirect('/new/game/%s' % contact.lead_id)

@app.route("/update/lead", methods=['POST'])
@auth_required('user')
def update_lead():
    form = LeadForm(request.form)
    if request.method == 'POST' and form.validate():
        lead = Lead.query.get(form.lead_id.data)
        lead.developer = form.developer.data
        lead.website = strip_http(form.website.data)
        lead.user_id = form.user_id.data
        lead.note = str(form.note.data)
        try:
            db.session.commit()
            app.logger.info("The lead %s was updated." % lead.developer)
            flash(u'Your lead was succesfully updated as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (lead.id, lead.developer), 'alert-success')
        except:
            flash('Something went wrong! We couldn\'t add your contact!', 'alert-danger')
            return redirect(url_for('update_lead'))
    return redirect('/lead/%s' % lead.id)

@app.route("/update/game", methods=['POST'])
@auth_required('user')
def update_game():
    form = GameForm(request.form)
    if request.method == 'POST':
        genders = []
        ages = []
        statuses = []
        # tags = []
        for item in form.genders.data:
            gender = Gender.query.filter_by(name=item).first()
            genders.append(gender)
        for item in form.ages.data:
            gender = Age.query.filter_by(name=item).first()
            ages.append(gender)
        for item in form.statuses.data:
            gender = Status.query.filter_by(name=item).first()
            statuses.append(gender)
        game = Game.query.get(form.game_id.data)
        game.name = form.name.data
        game.ratings = form.ratings.data
        game.ages = ages
        game.genders = genders
        game.statuses = statuses
        game.platform = form.platform.data
        game.lead_id = form.lead_id.data

        game.int_date = parse(form.int_date.data)
        try:
            db.session.commit()
            app.logger.info("The game %s was updated." % game.name)
            flash(u'Your game was succesfully updated as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (form.lead_id.data, game.name), 'alert-success')
        except:
            flash('Something went wrong! We couldn\'t add your game!', 'alert-danger')
            return redirect('/lead/%s' % form.lead_id.data)
    return redirect('/lead/%s' % form.lead_id.data)

@app.route("/update/contact", methods=['POST'])
@auth_required('user')
def update_contact():
    form = ContactForm(request.form)
    if request.method == 'POST' and form.validate():
        contact = Contact.query.get(form.contact_id.data)
        contact.name = form.name.data
        contact.email = form.email.data
        contact.phone = form.phone.data
        contact.title = form.title.data
        try:
            db.session.commit()
            app.logger.info("The contact %s was updated." % contact.name)
            flash(u'Your contact was succesfully updated as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (form.lead_id.data, contact.name), 'alert-success')
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % form.email.data, 'alert-warning')
            return redirect('/search?query=%s' % form.email.data)
        except:
            flash('Something went wrong! We couldn\'t add your contact!', 'alert-danger')
            return redirect('/lead/%s' % form.lead_id.data)
    return redirect('/lead/%s' % form.lead_id.data)


@app.route("/delete/game/<id>")
@auth_required('user')
def delete_game(id):
    game = Game.query.get(id)
    try:
        db.session.delete(game)
        db.session.commit()
        app.logger.info("The game %s was deleted." % game.name)
        db.session.flush()
        flash(u'The game %s was succesfully deleted' % (game.name), 'alert-danger')
    except:
        flash('Something went wrong! We couldn\'t delete your game!', 'alert-danger')
    return redirect('lead/%s' % game.lead_id)

@app.route("/delete/contact/<id>")
@auth_required('user')
def delete_contact(id):
    contact = Contact.query.get(id)
    try:
        db.session.delete(contact)
        db.session.commit()
        app.logger.info("The contact %s was deleted." % contact.name)
        db.session.flush()
        flash(u'The contact %s was succesfully deleted' % (contact.name), 'alert-danger')
    except:
        flash('Something went wrong! We couldn\'t delete your contact!', 'alert-danger')
    return redirect('lead/%s' % contact.lead_id)

@app.route("/delete/lead/<id>")
@auth_required('user')
def delete_lead(id):
    lead = Lead.query.get(id)
    for game in lead.games:
        game = Game.query.get(game.id)
        db.session.delete(game)
        app.logger.info("The game %s was deleted." % game.name)
        flash(u'The game %s was succesfully deleted' % (game.name), 'alert-danger')
    for contact in lead.contacts:
        contact = Contact.query.get(contact.id)
        db.session.delete(contact)
        app.logger.info("The contact %s was deleted." % contact.name)
        flash(u'The contact %s was succesfully deleted' % (contact.name), 'alert-danger')
    try:
        db.session.delete(lead)
        db.session.commit()
        app.logger.info("The lead %s was deleted." % lead.developer)
        db.session.flush()
        flash(u'The lead %s was succesfully deleted' % (lead.developer), 'alert-danger')
    except:
        flash('Something went wrong! We couldn\'t delete your lead!', 'alert-danger')
    return redirect(url_for('index'))

@app.route("/new/game/<id>")
@auth_required('user')
def new_game(id):
    lead = Lead.query.get_or_404(id)
    return render_template('new_game.html', lead=lead, attributes=get_attributes())

@app.route("/new/contact/<id>")
@auth_required('user')
def new_contact(id):
    lead = Lead.query.get_or_404(id)
    return render_template('new_contact.html', lead=lead)

@app.route("/new/lead")
@auth_required('user')
def new_lead():
    return render_template('new_lead.html')

@app.route("/lead/<id>/edit")
@auth_required('user')
def edit_lead(id):
    lead = Lead.query.get_or_404(id)
    user = User.query.get(lead.user_id)
    users = User.query.all()
    users.remove(user)
    return render_template('edit_lead.html', lead=lead, users=users, user=user, attributes=get_attributes())

@app.route("/lead/<id>")
@auth_required('user')
def lead(id):
    lead = Lead.query.get_or_404(id)
    user = User.query.get(lead.user_id)
    return render_template('lead.html', lead=lead, user=user, attributes=get_attributes())

@app.route("/user/<id>")
@auth_required('user')
def user(id):
    games = Game.query.order_by(Game.dau).options(joinedload('lead.user'))
    user = User.query.get_or_404(id)
    return render_template('user.html', user=user, games=games)

@app.route("/attributes", methods=['POST', 'GET'])
@auth_required('user')
def list_attributes():
    if request.method == 'GET':
        pass
    if request.method == 'POST':
        form = AttributeForm(request.form)
        if request.args.get('type') == 'status':
            item = Status.query.get(form.id.data)
        if request.args.get('type') == 'age':
            item = Age.query.get(form.id.data)
        if request.args.get('type') == 'gender':
            item = Gender.query.get(form.id.data)
        if request.args.get('type') == 'tag':
            item = Tag.query.get(form.id.data)
        item.name = form.name.data
        db.session.commit()
        flash('Succesfully update attribute %s' % item.name)
    return render_template('attributes.html', attributes=get_attributes())

@app.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'There was an issue with oauth: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    check_users = bool(me.data['id'] in settings.SAFE_USERS)
    # Check to see if the user's fb_id exists in the 'safe' list.
    # The safe list exists as an environment varaible called SAFE_USERS
    if check_users == False:
        flash(u'Access denied: You are not authorized to use this application.', 'alert-error')
        return redirect(url_for('index'))
    # Try to find the existing user. If they do not yet exist, create their account.
    try:
        # Query for the user
        user = User.query.filter_by(fb_id=me.data['id']).first()
        # set a cookie and put the user at the starting page.
        session['user'] = user.id
        flash(u'Welcome %s, you can begin by searching above for duplicate leads.' % me.data['name'], 'alert-success')
        app.logger.info("%s logged in." % me.data['name'])
        return redirect(url_for('index'))
    # If the user does not already exist, make them. We'll only get here
    # if their fb_id exists in the safe users list.
    except:
        user = User(fb_id=me.data['id'], name=me.data['name'], email=me.data['email'])
        try:
            db.session.add(user)
            db.session.commit()
            session['user'] = user.id
            session['name'] = user.name
            app.logger.info("An account was created for %s." % me.data['name'])
        except:
            flash(u'Error: We were unable to create your account.', 'alert-error')
            return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return facebook.authorize(callback=settings.FACEBOOK_CALLBACK + url_for('facebook_authorized',
        next=url_for('index')))

@app.route('/logout')
def logout():
    try:
        session.pop('user')
    except:
        flash(u"Looks like you tried to logout when you weren't logged in. Whoops!", 'alert-error')
    return redirect(url_for('index'))

def configure_raven(app):
    import os
    import traceback
    if 'SENTRY_DSN' in os.environ:
        try:
            from raven.contrib.flask import Sentry
            return Sentry(app)
        except Exception, e:
            print "Unexpected error:", e
            traceback.print_exc()

sentry = configure_raven(app)

if __name__ == "__main__":
    app.run(debug=settings.DEBUG, port=settings.PORT, host='0.0.0.0')
