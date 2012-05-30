from __future__ import division
import sendgrid
from datetime import date
from beagle import Game, Status, mailsend, datetimef, User, Lead
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('beagle', 'templates'))
env.filters['datetime'] = datetimef
template = env.get_template('pinger.html')

def get_leads(user=None, date=None):
	lead_query = Lead.query.filter(Lead.ping_date==date)
	leads = lead_query.filter(Lead.user_id==user.id)
	return leads

def render_template(leads, user):
	html = template.render(leads=leads, user=user)
	plain = "Who do you need to ping on %s?" % (todays_date())
	return html, plain

def get_users():
	users = User.query.all()
	return users

def get_user_leads(user):
	leads = get_leads(user, date.today())
	return leads

def send_message():
	users = get_users()
	for user in users:
		if len(user.leads) > 1:
			leads = get_user_leads(user)
			html, plain = render_template(leads, user)
			message = sendgrid.Message("beagle@kiip.me", "Leads to Ping for %s" % (todays_date()), plain, html)
			message.add_to(user.email, user.name)
			mailsend.web.send(message)

def todays_date():
	today = date.today()
	todays_date = today.strftime("%A, %B %d")
	return todays_date

if __name__ == "__main__":
	send_message()