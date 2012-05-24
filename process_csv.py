#!/usr/bin/env python

from beagle import *
import csv

FILENAME = './data.csv'

def main():
    print "Starting!"
    f = open(FILENAME, 'rU')
    reader = csv.reader(f)

    mapping = reader.next()

    for row in reader:
        count = 0
        obj = ObjectLead()
        for item in mapping:
            obj = process_ys(key=item, value=row[count], obj = obj)
            count  = count+1
        
        ret = obj.link_parts()
        print "Done row" 


def process_ys(key, value, obj):
    if key == 'Developer Name':
        obj.lead.developer = value

    elif key == 'Developer Website':
        obj.lead.website = value

    elif key == 'Contact Name':
        obj.contact.name = value

    elif key == 'Contact Email':
        obj.contact.email = value

    elif key == 'Contact Title':
        obj.contact.title = value

    elif key == 'Contact Phone':
        obj.contact.phone = value

    elif key == 'Game Name':
        obj.game.name = value

    elif key == 'Game Status':
        status = Status.query.filter_by(name = value).first()
        obj.game.status = status

    elif key == 'Game Platform':
        obj.game.platform = value

    elif key == 'Game DAU':
        pass

    elif key == 'Game Gender':
        pass

    elif key == 'Game Age':
        pass

    elif key == 'Integration Date (est. or date of prior integration)':
        pass

    elif key == 'Assigned Person':
        user = User.query.filter_by(name = value).first()
        obj.user = user

    else:
        print "Error! Something went wrong!"
        print "Key: %s, Value: %s" % key, value

    return obj


class ObjectLead:
    lead = None
    user = None
    game = None
    contact = None

    def __init__(self):
        self.lead = Lead()
        self.game = Game()
        self.contact = Contact()


    def link_parts(self):
       #  import pdb; pdb.set_trace()
        if self.user == None:
            print "Error: No Assigned Person"
            return -1

        e_lead = Lead.query.filter_by(developer = self.lead.developer).first()

        if e_lead:
            self.lead = e_lead
        
        else:
            self.lead.user = self.user
            self.lead.user_id = self.user.id
            db.session.add(self.lead)
            db.session.commit()


        ## This is shit. Serious shit. ##

        try:
            self.contact.lead = self.lead
            self.contact.lead_id = self.lead.id
            db.session.add(self.contact)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

        try:
            self.game.lead = self.lead
            self.game.lead_id = self.lead.id
            db.session.add(self.game)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
        
if __name__ == '__main__':
    main()
        
