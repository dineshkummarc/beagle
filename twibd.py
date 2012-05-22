import sendgrid
from datetime import date
from beagle import Game, Status, mailsend
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('beagle', 'templates'))

def todays_date():
	today = date.today()
	todays_date = today.strftime("%A, %B %d")
	return todays_date

def get_50000_games():
	status_ids = []
	status_ids.append(Status.query.filter_by(name="Integrating").first().id)
	status_query = Game.query.join('statuses').filter(Status.id.in_(status_ids)).distinct()
	games = status_query.filter(Game.dau>=50000).all()
	return games

def get_10000_games():
	status_ids = []
	status_ids.append(Status.query.filter_by(name="Testing").first().id)
	status_query = Game.query.join('statuses').filter(Status.id.in_(status_ids)).distinct()
	games = status_query.filter(Game.dau>=10000).all()
	return games

template = env.get_template('twibd.html')

html = template.render(games_10000=get_10000_games(), games_50000=get_50000_games())
plain = "The TWIBD Update for %s includes new games, live games and upcoming games." % (todays_date())

message = sendgrid.Message("beagle@kiip.me", "TWIBD Update for %s" % (todays_date()), plain, html)
message.add_to("jack@kiip.me", "Sales Team")
mailsend.web.send(message)