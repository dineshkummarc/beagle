import os
import redisco
import base64
from flask import Flask, request, redirect, url_for, session, flash, g, render_template
from flaskext.oauth import OAuth
from flaskext.redis import redis
from redisco import models

# environment variables

SAFE_USERS = os.environ.get("SAFE_USERS")
FACEBOOK_SECRET = str(os.environ.get("FACEBOOK_SECRET"))
FACEBOOK_CONSUMER = str(os.environ.get("FACEBOOK_CONSUMER"))
FACEBOOK_CALLBACK = str(os.environ.get("FACEBOOK_CALLBACK"))
PORT = int(os.environ.get("PORT", 5000))
APP_SECRET_KEY = str(os.environ.get("APP_SECRET_KEY"))
REDIS_HOST = str(os.environ.get("REDIS_HOST"))
REDIS_DB = int(os.environ.get("REDIS_DB"))
REDIS_PORT = int(os.environ.get("REDIS_PORT"))

# initialize the things

app = Flask(__name__)
oauth = OAuth()
app.secret_key = APP_SECRET_KEY
redisco.connection_setup(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# base model

class Lead(models.Model):
    ident = models.Attribute(required=True, unique=True, indexed=True)
    name = models.Attribute(required=True, unique=True)
    owner = models.Attribute(required=True)
    games = models.ListField(str)
    created_at = models.DateTimeField(auto_now_add=True)   

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

@app.route("/add")
def add():
    if request.method == 'POST':
        game = []
        name = request.form['name']
        game = request.form['games']
        ident = base64.urlsafe_b64encode(name)
        owner = session['facebook_user'][0]
        try:
            foo = 'bar'
        except Exception:
            flash('',  'warning')
        flash('', 'success')

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
        flash(u'Access denied: You are not authorized to use this application.', 'error')
        return redirect(url_for('hello'))
    session['facebook_user'] = [me.data['id'], me.data['name']]
    flash(u'Welcome %s, you can begin by searching above for duplicate leads.' % me.data['name'], 'success')
    return redirect(url_for('hello'))
    
@app.route('/login')
def login():
    return facebook.authorize(callback=FACEBOOK_CALLBACK + url_for('facebook_authorized',
        next=url_for('hello')))

@app.route('/logout')
def logout():
    session.pop('facebook_user')
    return redirect(url_for('hello'))
    
if __name__ == "__main__":
    app.run(debug=True, port=PORT, host='0.0.0.0')