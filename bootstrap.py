from beagle import Gender, Age, Tag, Status, Game, Lead, db, User, Contact
import datetime
import random

users = ['Jack', 'Nick', 'Yong-Soo', 'Steve']

game_name_prefix = ['Awesome', 'Fun', 'Hot', 'Super', 'Amazing', '']
game_name_genre = ['Pirate', 'Zombie', 'Management', 'Alien', 'People', 'Tower', 'Shop', '']
game_name_postfix = ['Adventure', 'Experience', 'Game', 'Tower', 'Street', '3D', 'Kart']

lead_name_prefix = ['Big', 'Fun', 'Zynga', 'Armor', 'Viking', 'Haha', 'M', 'Z']
lead_name_postfix = ['Co', 'Inc', 'Company', 'Family', 'Group', 'Corp', '', 'Ltd']

random.seed()

def fill_db():
    plat_attr = ['iOS', 'Android', 'Web']
    age_attr = [Age('13-20'), Age('22-35'), Age('26-34'), Age('35-55'), Age('55+')]
    gen_attr = [Gender('Male'), Gender('Female')]
    stat_attr = [Status('Initial Discussion'), Status('Delayed Integration'), Status('Integrating'), Status('Testing'), Status('Live'), Status('Dormant')]
    tag_attr =[Tag('Featured'), Tag('Spotlight')]

    attributes = tag_attr + stat_attr + gen_attr + age_attr

    for attribute in attributes:
        db.session.add(attribute)
        db.session.commit()

    print "Adding users"
    count = 0
    for user in users:
        user = User('11111%s' % count, user, '%s@kiip.me' % user)
        db.session.add(user)
        db.session.commit()
        count = count+1

    print "Adding leads"
    leads = []
    for lead in range(0, 30):
        userc = random.choice(users)
        user = User.query.filter_by(name = userc).first()
        leadprefix = random.choice(lead_name_prefix)
        leadname = random.choice(game_name_prefix)+" " +leadprefix+" "+random.choice(lead_name_postfix)
        lead = Lead(leadname, 'dev@%s.com' % leadprefix, user.id)
        leads.append(lead)
        db.session.add(lead)
        db.session.commit()

    print "Adding games"
    for game in range(0, 50):
        lead = random.choice(leads)
        ages = get_selection(age_attr)
        genders = get_selection(gen_attr)
        statuses = [random.choice(stat_attr)]
        tags = get_selection(tag_attr)
        platform = random.choice(plat_attr)
        gamename = random.choice(game_name_prefix)+" "+random.choice(game_name_genre)+" "+random.choice(game_name_postfix)
        ratings = random.randint(0, 10000)
        game = Game(gamename, lead.id, ratings, platform, ages, genders, statuses, tags, datetime.datetime.utcnow())
        db.session.add(game)
        db.session.commit()

    print "Adding contacts"
    count = 0
    for contact in range(0, 40):
        lead = random.choice(leads)
        contact = Contact(lead.id, 'Contact Name', 'contact%s@example.com' % count, '4155087396', 'Title')
        db.session.add(contact)
        db.session.commit()
        count = count+1

def get_selection(attr):
    selection = []
    num = random.randint(0, len(attr)-1)
    for item in range(0, num):
        selection.append(random.choice(attr))
    return selection

try:
    print "Trying to drop exisiting database."
    db.drop_all()
    print "Exisiting database dropped."
    db.create_all()
    print "Database created."
    fill_db()
    print "Done!"
except:
    db.create_all()
    fill_db()
    print "No exisiting Database, creating one"
