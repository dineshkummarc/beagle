#### The Beagle is a simple [CRM](http://en.wikipedia.org/wiki/Customer_relationship_management)

kidding It is a _work in progress_! But works pretty well so far.

### How to use

#### Get the code

	$ git clone https://github.com/pearkes/beagle
    $ heroku create --stack cedar

#### Add the Configuration Variables on Heroku

	$ heroku config:add SAFE_USERS=[66666, 77777]
	$ heroku config:add FACEBOOK_CONSUMER=1515115151515
	$ heroku config:add FACEBOOK_SECRET=af737a83tg9a38af9a38fa3
	$ heroku config:add APP_SECRET_KEY=areallysecretkey
	$ heroku config:add FACEBOOK_CALLBACK=http://yourcrm.herokuapp.com/
	$ heroku config:add DEBUG=False
	$ heroku config:add STATIC_PATH=/static
	$ heroku config:add RATINGS_MULTIPLIER=1.8

#### Deploy the App

    $ git push heroku master

#### Local

	$ gem install foreman
	$ pip install -r requirements.txt
	$ foreman start
	18:38:25 web.1     | started with pid 1
	18:38:26 web.1     |  * Running on http://0.0.0.0:5000/
	18:38:26 web.1     |  * Restarting with reloader

#### TODO

- Add Gunicorn for production.
