import os
import base64
import uuid
import datetime
from flask import Flask, request, redirect, url_for, session, flash, g, render_template
from flaskext.oauth import OAuth
from flaskext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# environment variables

SAFE_USERS = os.environ.get("SAFE_USERS")
FACEBOOK_SECRET = str(os.environ.get("FACEBOOK_SECRET"))
FACEBOOK_CONSUMER = str(os.environ.get("FACEBOOK_CONSUMER"))
FACEBOOK_CALLBACK = str(os.environ.get("FACEBOOK_CALLBACK"))
PORT = int(os.environ.get("PORT", 5000))
APP_SECRET_KEY = str(os.environ.get("APP_SECRET_KEY"))
DEBUG = os.environ.get("DEBUG")
DATABASE_URL=str(os.environ.get("DATABASE_URL"))

# initialize the things

app = Flask(__name__)
oauth = OAuth()
app.secret_key = APP_SECRET_KEY
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db = SQLAlchemy(app)

# base model

class Lead(db.Model):
    ident = db.Column(db.String(80), primary_key=True)
    developer = db.Column(db.String(80), unique=False)
    name = db.Column(db.String(80), unique=False)
    email = db.Column(db.String(80), unique=True)
    owner = db.Column(db.String(80), unique=False)
    games = db.Column(db.String(160), unique=False)
    pubdate = db.Column(db.DateTime)
    
    def __init__(self, developer, name, email, owner, games, pubdate=None, ident=None):
        self.developer = developer
        self.name = name
        self.email = email
        self.owner = owner
        self.games = str(games)
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
    consumer_key=FACEBOOK_CONSUMER,
    consumer_secret=FACEBOOK_SECRET
)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

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
def search():
    print request.args['query']
    return render_template('results.html')

@app.route("/owner")
def owner():
    print request.args['name']
    return render_template('results.html')

@app.route("/add", methods=['POST'])
def add():
    if request.method == 'POST':
        developer = request.form['developer']
        games = request.form['games']
        name = request.form['name']
        email = request.form['email']
        owner = session['facebook_user'][1]
        lead = Lead(developer=developer, name=name, email=email, owner=owner, games=games)
        try:
            db.session.add(lead)
            db.session.commit()
            flash(u'Your lead was succesfully saved as <strong><a href=\"/lead/%s\">%s</a></strong>. It\'s automatically been assigned to you.' % (lead.ident, developer), 'alert-success')            
        except IntegrityError:
            flash('Looks like <strong>%s</strong> was a duplicate. Search results are below!' % email, 'alert-warning')            
            return redirect('%s?query=%s' % (url_for('search'), email))
        return redirect(url_for('new'))

@app.route("/new")
def new():
    return render_template('new.html')

@app.route("/lead/<ident>")
def lead(ident):
    lead = Lead.query.filter_by(ident=ident).first_or_404()
    return render_template('lead.html', lead=lead)

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
    safe_users = SAFE_USERS
    check_users = bool(me.data['id'] in SAFE_USERS)
    if check_users == False:
        flash(u'Access denied: You are not authorized to use this application.', 'alert-error')
        return redirect(url_for('hello'))
    session['facebook_user'] = [me.data['id'], me.data['name']]
    flash(u'Welcome %s, you can begin by searching above for duplicate leads.' % me.data['name'], 'alert-success')
    return redirect(url_for('hello'))
    
@app.route('/login')
def login():
    return facebook.authorize(callback=FACEBOOK_CALLBACK + url_for('facebook_authorized',
        next=url_for('hello')))

@app.route('/logout')
def logout():
    try:
        session.pop('facebook_user')
    except:
        flash(u"Looks like you tried to logout when you weren't logged in. Whoops!", 'alert-error')
    return redirect(url_for('hello'))
    
if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT, host='0.0.0.0')