import unittest
from google.appengine.ext import db
from google.appengine.ext import testbed
from google.appengine.api import users


class BaseTestCase(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    
    self.testbed.activate()
    
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_user_stub()
    
    
    
  def tearDown(self):
    self.testbed.deactivate()
    
  def assert200(self, response):
    self.assertEqual(response.status_int, 200, msg="Got {0} instead".format(response.status_int))
      