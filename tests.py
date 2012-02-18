import os
import beagle
import unittest
import uuid

class BeagleTestCase(unittest.TestCase):

    def setUp(self):
        beagle.app.config['TEMP_DIR'] = '/tmp/%stest.db' % uuid.uuid4()
        beagle.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % beagle.app.config['TEMP_DIR']
        beagle.app.config['TESTING'] = True
        self.app = beagle.app.test_client()
        beagle.db.create_all()

    def tearDown(self):
        os.remove(beagle.app.config['TEMP_DIR'])

if __name__ == '__main__':
    unittest.main()