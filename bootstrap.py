from beagle import db
from beagle import app
import os


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
try:
	print "Trying to drop exisiting database."
	db.drop_all()
	print "Exisiting database dropped."
	db.create_all()
	print "Database created."
except:
	db.create_all()
	print "No exisiting Database, creating one"

