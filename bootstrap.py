from beagle import db
from beagle import app

try:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    db.create_all()
    print "Database created"
except Exception:
    print "FAIL! Unable to create database"