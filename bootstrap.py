from beagle import db
from beagle import app
import os


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db.create_all()
print "Database created"