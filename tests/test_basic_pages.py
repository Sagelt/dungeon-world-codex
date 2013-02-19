import unittest
from monsterrules.common import Monster, Profile
import main
import basetest


class CreateTestCase(basetest.BaseTestCase):
      
  def test_get(self):
    response = main.app.get_response('/monster/create')
    self.assert200(response)


class HomeTestCase(basetest.BaseTestCase):
      
  def test_get(self):
    response = main.app.get_response('/')
    self.assert200(response)


class ViewTestCase(basetest.BaseTestCase):
      
  def test_get(self):
    creator = Profile().put()
    monster = Monster()
    monster.creator = creator
    monster.put()
    
    response = main.app.get_response('/monster/'+str(monster.key().id()))
    self.assert200(response)