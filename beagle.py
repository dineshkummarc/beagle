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
    name = db.Column(db.String(80), index=True)
    email = db.Column(db.String(80), unique=True, index=True)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))

    user = db.relationship(User, backref='leads', lazy='joined')

    def __init__(self, developer=developer, name=name, email=email, user_id=user_id, id=None):
        self.developer = developer
        self.name = name
        self.email = email
        self.user_id = user_id
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')

class Game(db.Model):
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), index=True)
    lead_id = db.Column(db.String(36), db.ForeignKey('lead.id'))
    status = db.Column(db.String(80), index=True)
    ratings = db.Column(db.Integer)
    dau = db.Column(db.Integer)
    age = db.Column(db.String(80))
    gender = db.Column(db.String(80))
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow(), onupdate=datetime.datetime.utcnow(), index=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow(), index=True)

    lead = db.relationship(Lead, backref='games', lazy='joined')

    def __init__(self, name=name, lead_id=lead_id, status=status, ratings=ratings, age=age, gender=gender, dau=None, id=None):
        self.name = name
        self.lead_id = lead_id
        self.status = status
        self.ratings = ratings
        self.gender = gender
        self.age = age
        if dau is None:
            self.dau = float(self.ratings) * float(settings.RATINGS_MULTIPLIER)
        if id is None:
            self.id = str(uuid.uuid4()).replace('-', '')

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
    leads = lead_query.limit(10).all()
    leads = Lead.query.filter(Lead.developer.like("%" + query + "%")).all()
    leads += Lead.query.filter(Lead.email.like("%" + query + "%")).all()
    leads += Lead.query.filter(Lead.name.like("%" + query + "%")).all()
    unq_leads = dict([(l.id, l) for l in leads])
    leads = unq_leads.values()
    games = Game.query.filter(Game.name.like("%" + query + "%")).all()
    return render_template('search.html', leads=leads, games=games)

@app.route("/browse")
@auth_required('user')
def browse():
    if request.args:
        gender = request.args.get('gender')
        age = request.args.get('age')
        status = request.args.get('status')
        games = Game.query.filter_by(age=age, gender=gender, status=status)
    else:
        games = []
    return render_template('browse.html', games=games)

@app.route("/add/lead", methods=['POST'])
@auth_required('user')
def add_lead():
    if request.method == 'POST':
        developer = request.form['developer']
        email = request.form['email']
        name = request.form['name']
        user_id = session['user']
        lead = Lead(developer=developer, name=name, email=email, user_id=user_id)
        try:
            db.session.add(lead)
            db.session.commit()
            flash(u'Your lead was succesfully saved as <strong><a href=\"/lead/%s\">%s</a></strong>. It\'s automatically been assigned to you. Add a game below.' % (lead.id, lead.developer), 'alert-success')
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % email, 'alert-warning')
            return redirect('%s?query=%s' % (url_for('search'), email))
        return redirect('/new/game/%s' % lead.id)

@app.route("/update/lead", methods=['POST'])
@auth_required('user')
def update_lead():
    if request.method == 'POST':
        lead_id = request.form['lead_id']
        developer = request.form['developer']
        email = request.form['email']
        name = request.form['name']
        user_id = session['user']
        lead = Lead.query.get(lead_id)
        lead.developer = developer
        lead.email = email
        lead.name = name
        lead.user_id = user_id
        try:
            db.session.commit()
            flash(u'Your lead was succesfully updated as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (lead.id, lead.developer), 'alert-success')
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % email, 'alert-warning')
            return redirect('%s?query=%s' % (url_for('search'), email))
        return redirect('/lead/%s' % lead.id)

@app.route("/add/game", methods=['POST'])
@auth_required('user')
def add_game():
    if request.method == 'POST':
        lead_id = request.form['lead_id']
        name = request.form['name']
        status = request.form['status']
        ratings = request.form['ratings']
        age = request.form['age']
        gender = request.form['gender']
        game = Game(name=name, lead_id=lead_id, status=status, ratings=ratings, age=age, gender=gender)
        try:
            db.session.add(game)
            db.session.commit()
            flash(u'Your game was succesfully saved as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (lead_id, game.name), 'alert-success')
        except IntegrityError:
            flash('Something went wrong! We couldn\'t add your game!', 'alert-danger')
        return redirect(url_for('lead', id=lead_id))

@app.route("/update/game", methods=['POST'])
@auth_required('user')
def update_game():
    if request.method == 'POST':
        lead_id = request.form['lead_id']
        game_id = request.form['game_id']
        name = request.form['name']
        status = request.form['status']
        ratings = request.form['ratings']
        age = request.form['age']
        gender = request.form['gender']
        game = Game.query.get(game_id)
        game.name = name
        game.status = status
        game.ratings = ratings
        game.age = age
        game.gender = gender
        try:
            db.session.commit()
            flash(u'Your game was succesfully updated as <strong><a href=\"/lead/%s\">%s</a></strong>.' % (lead_id, game.name), 'alert-success')
        except IntegrityError:
            flash('Something went wrong! We couldn\'t add your game!', 'alert-danger')
        return redirect(url_for('lead', id=lead_id))

@app.route("/delete/game/<id>")
@auth_required('user')
def delete_game(id):
    game = Game.query.get(id)
    try:
        db.delete(game)
        db.session.commit()
        db.session.flush()
        flash(u'The game %s was succesfully deleted' % (game.name), 'alert-danger')
    except:
        flash('Something went wrong! We couldn\'t delete your game!', 'alert-danger')
    return redirect(url_for('index'))

@app.route("/new/game/<id>")
@auth_required('user')
def new_game(id):
    lead = Lead.query.get_or_404(id)
    return render_template('new_game.html', lead=lead)

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