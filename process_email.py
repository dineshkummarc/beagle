#!/usr/bin/env python

# Some magic shit goes on here

import imaplib
from bs4 import BeautifulSoup
from beagle import * # I'm sorry Jack

# open connection
def get_emails():
    m = imaplib.IMAP4_SSL('imap.gmail.com')
    m.login('beagle@kiip.me', 'kiipitreal')
    m.select()
    resp, data = m.search(None, "FROM", "nick@kiip.me")
    emails = []
    for item in data[0].split():
        resp, data = m.fetch(item, '(RFC822)')
        emails.append(data[0][1])

    print len(emails)
    return emails
# still need to delete emails

def process_email(email):
    soup = BeautifulSoup(email)
    divs = soup.find_all('div')

    data = []
    if len(divs) == 4:
        for div in divs:
            text = div.text
            text = text.split(':')[1].strip()
            data.append(text)

    else:
        print "Failed to parse"

    return data

def add_lead(data):
    lead = Lead(developer=data[0], website=None)
    user = User.query.filter_by(name = data[3]).first()
    if user == None:
        print "User not found!"
        return data
    
    lead.user = user
    lead.user_id = user.id
    db.session.add(lead)
    db.session.commit()
    data.append(lead)
    return data

def add_contact(data):
    if len(data) == 5:
        lead = data[4]
        contact = Contact(lead_id = lead.id, name=data[1], email=data[2])
        contact.phone = None
        contact.title = None
        db.session.add(contact)
        db.session.commit()

def get_test_emails():
    f = open('./sample_email', 'r').read()
    emails = [f]
    return emails

def main():
#    emails = get_emails()
    emails = get_test_emails()
    for email in emails:
        data = process_email(email)
        data = add_lead(data)
        data = add_contact(data)


if __name__ == "__main__":
    main()
