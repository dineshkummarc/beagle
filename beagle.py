import os
import base64
import uuid
import datetime
import settings
from flask import Flask, request, redirect, url_for, session, flash, g, render_template
from flaskext.oauth import OAuth
from flaskext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from functools import wraps

# initialize the things

app = Flask(__name__)
oauth = OAuth()
app.secret_key = settings.APP_SECRET_KEY
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
db = SQLAlchemy(app)

# base model

class Lead(db.Model):
    ident = db.Column(db.String(80), primary_key=True)
    developer = db.Column(db.String(80), unique=False)
    name = db.Column(db.String(80), unique=False)
    email = db.Column(db.String(80), unique=True)
    owner = db.Column(db.String(80), unique=False)
    games = db.Column(db.String(160), unique=False)
    status = db.Column(db.String(80), unique=False)
    ratings = db.Column(db.Integer, unique=False)
    dau = db.Column(db.Integer, unique=False)
    age = db.Column(db.String(80), unique=False)
    gender = db.Column(db.String(80), unique=False)
    pubdate = db.Column(db.DateTime, unique=False)
    
    def __init__(self, developer, name, email, owner, games, status, ratings, age, gender, dau=None, pubdate=None, ident=None):
        self.developer = developer
        self.name = name
        self.email = email
        self.owner = owner
        self.games = str(games)
        self.status = status
        self.ratings = ratings
        self.age = age
        self.gender = gender
        if dau is None:
            self.dau = float(ratings) * float(settings.RATINGS_MULTIPLIER)
        if pubdate is None:
            self.pubdate = datetime.datetime.utcnow()
        if ident is None:
            self.ident = str(uuid.uuid4()).replace('-', '')
        
    def __repr__(self):
        return '<IDENT: %r NAME: %r OWNER: %r GAMES: %r>' % (self.ident, self.name, self.owner, self.games)


# oauth settings (this can be pretty easily swapped out for twitter/github/etc.)

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=settings.FACEBOOK_CONSUMER,
    consumer_secret=settings.FACEBOOK_SECRET
)

# decorators

def auth_required(role):
    def decorator(f):
        @wraps(f)
        def inner(*a, **kw):
            if not session.get('facebook_user'):
                flash(u'<strong>Access denied:</strong> You must be logged in to use this application.', 'alert-error')
                return redirect(url_for('hello'))
            elif session['facebook_user'][0] in settings.SAFE_USERS:
                return f(*a, **kw)
            else:
                flash('<strong>Access denied:</strong> You must be logged in to use this application.', 'alert-error')
                return redirect(url_for('hello'))
        return inner
    return decorator
    
@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

# views

@app.route("/")
def hello():
    try:
        user = session['facebook_user']
        user_name = user[1]
        user_id = user[0]
    except Exception:
        return render_template('login.html')
    return render_template('index.html', user_name=user_name, user_id=user_id)

@app.route("/search")
@auth_required('user')
def search():
    print request.args['query']
    return render_template('results.html')

@app.route("/owner")
@auth_required('user')
def owner():
    print request.args['name']
    return render_template('results.html')

@app.route("/add", methods=['POST'])
@auth_required('user')
def add():
    if request.method == 'POST':
        developer = request.form['developer']
        games = request.form['games']
        email = request.form['email']
        name = request.form['name']
        status = request.form['status']
        ratings = request.form['ratings']
        age = request.form['age']
        gender = request.form['gender']    
        owner = session['facebook_user'][1]
        lead = Lead(developer=developer, name=name, email=email, games=games, status=status, ratings=ratings, age=age, gender=gender, owner=owner)
        try:
            db.session.add(lead)
            db.session.commit()
            flash(u'Your lead was succesfully saved as <strong><a href=\"/lead/%s\">%s</a></strong>. It\'s automatically been assigned to you.' % (lead.ident, developer), 'alert-success')            
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % email, 'alert-warning')            
            return redirect('%s?query=%s' % (url_for('search'), email))
        return redirect(url_for('new'))

@app.route("/new")
@auth_required('user')
def new():
    return render_template('new.html')

@app.route("/lead/<ident>")
@auth_required('user')
def lead(ident):
    lead = Lead.query.filter_by(ident=ident).first_or_404()
    funnel = {'Dormant': '0', 'Inital Discussion': '20', 'Delayed Integration': '50', 'Integrating' : '80', 'Testing': '90', 'Live': '100'}
    funnel_status = funnel[lead.status]
    return render_template('lead.html', lead=lead, funnel_status=funnel_status)
    
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
    if check_users == False:
        flash(u'Access denied: You are not authorized to use this application.', 'alert-error')
        return redirect(url_for('hello'))
    session['facebook_user'] = [me.data['id'], me.data['name']]
    flash(u'Welcome %s, you can begin by searching above for duplicate leads.' % me.data['name'], 'alert-success')
    return redirect(url_for('hello'))
    
@app.route('/login')
def login():
    return facebook.authorize(callback=settings.FACEBOOK_CALLBACK + url_for('facebook_authorized',
        next=url_for('hello')))

@app.route('/logout')
def logout():
    try:
        session.pop('facebook_user')
    except:
        flash(u"Looks like you tried to logout when you weren't logged in. Whoops!", 'alert-error')
    return redirect(url_for('hello'))

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