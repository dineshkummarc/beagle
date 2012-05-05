from beagle import db, app, User, Game, Lead, Contact, Tag, Age, Gender, Status
import datetime

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
rando = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

def fill_db():
	# do the initial attributes
	attributes = [Age('13-20'), Age('22-35'), Age('26-34'), Age('35-55'), Age('55+'), Gender('Male'), Gender('Female'), Status('Initial Discussion'), Status('Delayed Integration'), Status('Integrating'), Status('Testing'), Status('Live'), Status('Dormant'), Tag('Featured'), Tag('Spotlight')]
	for attribute in attributes:
		db.session.add(attribute)
		db.session.commit()
	for rand in rando:
		user = User('11111%s' % rand, 'User Name %s' % rand, 'user%s@kiip.me' % rand)
		db.session.add(user)
		db.session.commit()
	for rand in rando:
		user = User.query.filter_by(name='User Name %s' % rand).first()
		lead = Lead('Developer %s' % rand, 'kiip%s.me' % rand, user.id)
		db.session.add(lead)
		db.session.commit()
	for rand in rando:
		lead = Lead.query.filter_by(developer='Developer %s' % rand).first()
		ages = [Age.query.filter_by(name='13-20').first()]
		genders = [Gender.query.filter_by(name='Male').first(), Gender.query.filter_by(name='Female').first()]
		statuses = [Status.query.filter_by(name='Initial Discussion').first()]
		tags = [Tag.query.filter_by(name='Featured').first()]
		game = Game('Game %s' % rand, lead.id, 1500, 'iOS', ages, genders, statuses, tags, datetime.datetime.utcnow())
		db.session.add(game)
		db.session.commit()
	for rand in rando:
		lead = Lead.query.filter_by(developer='Developer %s' % rand).first()
		contact = Contact(lead.id, 'Contact Name %s' % rand, 'contact%s@kiip.me' % rand, '4155087396%s' % rand, 'Title %s' % rand)
		db.session.add(contact)
		db.session.commit()

try:
	print "Trying to drop exisiting database."
	db.drop_all()
	print "Exisiting database dropped."
	db.create_all()
	print "Database created."
	fill_db()
except:
	db.create_all()
	fill_db()
	print "No exisiting Database, creating one"
