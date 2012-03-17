import os
import base64
import uuid
import datetime
import settings
from flask import Flask, request, redirect, url_for, session, flash, g, render_template
from flaskext.oauth import OAuth
from flaskext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from functools import wraps
from wtforms import Form, BooleanField, TextField, PasswordField, validators, IntegerField


# initialize the things

app = Flask(__name__)
oauth = OAuth()
app.secret_key = settings.APP_SECRET_KEY
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
db = SQLAlchemy(app)

# base model
# todo

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    fb_id = db.Column(db.String(80))
    name = db.Column(db.String(160))
    email = db.Column(db.String(80))

    def __init__(self, fb_id=fb_id, name=name, email=email, id=None):
        self.fb_id = fb_id
        self.name = name
        self.email = email
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')

class Lead(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    developer = db.Column(db.String(80), index=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    website = db.Column(db.String(200), index=True)
    note = db.Column(db.LargeBinary)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))

    user = db.relationship(User, backref='leads', lazy='joined')

    def __init__(self, developer=developer, website=website, user_id=user_id, note=None, id=None):
        self.developer = developer
        self.website = website
        self.note = note
        self.user_id = user_id
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')

class Contact(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), index=True)
    email = db.Column(db.String(80), unique=True, index=True)
    phone = db.Column(db.String(80), index=True)
    title = db.Column(db.String(120), index=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    lead_id = db.Column(db.String(36), db.ForeignKey('lead.id'))

    lead = db.relationship(Lead, backref='contacts', lazy='joined')

    def __init__(self, lead_id=lead_id, name=name, email=email, phone=phone, title=title, id=None):
        self.lead_id = lead_id
        self.name = name
        self.email = email
        self.title = title
        self.phone = phone
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')

class Game(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(80), index=True)
    status = db.Column(db.String(80), index=True)
    ratings = db.Column(db.Integer)
    dau = db.Column(db.Integer)
    age = db.Column(db.String(80))
    gender = db.Column(db.String(80))
    platform = db.Column(db.String(80))
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    lead_id = db.Column(db.String(36), db.ForeignKey('lead.id'))

    lead = db.relationship(Lead, backref='games', lazy='joined')

    def __init__(self, name=name, lead_id=lead_id, status=status, ratings=ratings, age=age, gender=gender, platform=platform, dau=None, id=None):
        self.name = name
        self.lead_id = lead_id
        self.status = status
        self.ratings = ratings
        self.gender = gender
        self.age = age
        self.platform = platform
        if dau is None:
            self.dau = int(self.ratings * float(settings.RATINGS_MULTIPLIER))
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')

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
    status = TextField('status')
    ratings = IntegerField('ratings')
    age = TextField('age')
    gender = TextField('gender')
    platform = TextField('platform')

class ContactForm(Form):
    lead_id = TextField('lead_id')
    name = TextField('name')
    email = TextField('email')
    phone = TextField('phone')
    title = TextField('title')

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
    lead_query = Lead.query.order_by(Lead.created).options(joinedload('user'))
    leads = lead_query.limit(10).all()
    game_query = Game.query.order_by(Game.created).options(joinedload('lead.user'))
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
    games = Game.query.filter(Game.name.like("%" + query + "%")).all()
    return render_template('search.html', leads=leads, games=games, contacts=contacts)

@app.route("/browse")
@auth_required('user')
def browse():
    if request.args:
        gender = request.args.get('gender')
        age = request.args.get('age')
        status = request.args.get('status')
        games = Game.query.filter_by()
        if gender: games = games.filter_by(gender=gender)
        if age: games = games.filter_by(age=age)
        if status: games = games.filter_by(status=status)
        return render_template('browse.html', games=games)
    return render_template('browse.html', request.args=request.args)

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
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % form.email.data, 'alert-warning')
            return redirect('%s?query=%s' % (url_for('search'), form.email.data))
    return redirect('/new/contact/%s' % lead.id)

@app.route("/add/game", methods=['POST'])
@auth_required('user')
def add_game():
    form = GameForm(request.form)
    if request.method == 'POST' and form.validate():
        game = Game(form.name.data, form.lead_id.data, form.status.data, form.ratings.data, form.age.data, form.gender.data, form.platform.data)
        try:
            db.session.add(game)
            db.session.commit()
            app.logger.info("The game %s was added." % game.name)
            flash(u'Your game was succesfully saved as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (game.lead_id, game.name), 'alert-success')
        except IntegrityError:
            flash('Something went wrong! We couldn\'t add your game!', 'alert-danger')
        return redirect('/lead/%s' % game.lead_id)

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
            flash('Something went wrong! We couldn\'t add your contact!', 'alert-danger')
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
        lead.note = form.note.data
        try:
            db.session.commit()
            app.logger.info("The lead %s was updated." % lead.developer)
            flash(u'Your lead was succesfully updated as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (lead.id, lead.developer), 'alert-success')
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % form.email.data, 'alert-warning')
            return redirect('%s?query=%s' % (url_for('search'), form.email.data))
    return redirect('/lead/%s' % lead.id)

@app.route("/update/game", methods=['POST'])
@auth_required('user')
def update_game():
    form = GameForm(request.form)
    if request.method == 'POST' and form.validate():
        game = Game.query.get(form.game_id.data)
        game.name = form.name.data
        game.status = form.status.data
        game.ratings = form.ratings.data
        game.age = form.age.data
        game.gender = form.gender.data
        game.platform = form.platform.data
        game.lead_id = form.lead_id.data
        try:
            db.session.commit()
            app.logger.info("The game %s was updated." % game.name)
            flash(u'Your game was succesfully updated as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (form.lead_id.data, game.name), 'alert-success')
        except IntegrityError:
            flash('Something went wrong! We couldn\'t add your game!', 'alert-danger')
            return redirect('/lead/%s' % form.lead_id.data)
    return redirect('/lead/%s' % form.lead_id.data)

@app.route("/update/contact", methods=['POST'])
@auth_required('user')
def update_contact():
    form = GameForm(request.form)
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
    return render_template('new_game.html', lead=lead)

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
    return render_template('edit_lead.html', lead=lead, users=users, user=user)

@app.route("/lead/<id>")
@auth_required('user')
def lead(id):
    lead = Lead.query.get_or_404(id)
    user = User.query.get(lead.user_id)
    return render_template('lead.html', lead=lead, user=user)

@app.route("/user/<id>")
@auth_required('user')
def user(id):
    games = Game.query.order_by(Game.dau).options(joinedload('lead.user'))
    user = User.query.get_or_404(id)
    return render_template('user.html', user=user, games=games)


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
    safe_users = settings.SAFE_USERS
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