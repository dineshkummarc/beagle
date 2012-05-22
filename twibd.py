from __future__ import division
import sendgrid
from datetime import date
from beagle import Game, Status, mailsend, datetimef, User
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

def get_user_percentage():
	user_data = []
	users = []
	all_users = User.query.all()
	for user in all_users:
		if len(user.leads) > 2:
			users.append(user)
	total_games = len(Game.query.all())
	for user in users:
		number_games = 0
		for lead in user.leads:
			number_games = number_games + len(lead.games)
		game_percentage = (number_games / total_games) * 100
		user_specific = {user.name: round(game_percentage)}
		user_data.append(user_specific)
	return user_data

def make_chart_url():
	users = []
	percentages = []
	user_data = get_user_percentage()
	for user in user_data:
		users.append(user.keys()[0])
		percentages.append(user.values()[0])
	percentages = ','.join(map(str, percentages))
	users = '|'.join(map(str, users))
	url = "https://chart.googleapis.com/chart?cht=p3&chd=t:%s&chs=350x150&chl=%s" % (percentages, users)
	return url

template = env.get_template('twibd.html')

html = template.render(games_10000=get_games(10000, "Testing"), games_50000=get_games(50000, "Integrating"), url=make_chart_url())

plain = "The TWIBD Update for %s includes new games, live games and upcoming games." % (todays_date())

message = sendgrid.Message("beagle@kiip.me", "TWIBD Update for %s" % (todays_date()), plain, html)
message.add_to("jack@kiip.me", "Sales Team")
mailsend.web.send(message)