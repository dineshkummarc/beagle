import sendgrid
from datetime import date
from beagle import Game, Status, mailsend, datetimef
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('beagle', 'templates'))
env.filters['datetime'] = datetimef

def get_games(dau=None, status=None):
	status_ids = []
	status_ids.append(Status.query.filter_by(name=status).first().id)
	status_query = Game.query.join('statuses').filter(Status.id.in_(status_ids)).distinct()
	games = status_query.filter(Game.dau>=dau).all()
	return games

def todays_date():
	today = date.today()
	todays_date = today.strftime("%A, %B %d")
	return todays_date

template = env.get_template('twibd.html')

html = template.render(games_10000=get_games(10000, "Testing"), games_50000=get_games(50000, "Integrating"))

plain = "The TWIBD Update for %s includes new games, live games and upcoming games." % (todays_date())

message = sendgrid.Message("beagle@kiip.me", "TWIBD Update for %s" % (todays_date()), plain, html)
message.add_to("jack@kiip.me", "Sales Team")
mailsend.web.send(message)