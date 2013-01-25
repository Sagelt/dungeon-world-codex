#!/usr/bin/env python
#
# Copyright 20013 Sage LaTorra
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import urllib
import os
import cgi
from monsterrules.core.builder import CoreMonsterBuilder
from monsterrules.common import Monster, Profile
from google.appengine.ext import db
from google.appengine.api import users

jinja_environment = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))


class MainPage(webapp2.RequestHandler):
  """Renders the main page.
  
  Retrieves monsters to be displayed in promotional areas. Currently that
  means the 10 most recent.
  
  Templates used: index.html"""
  
  def get(self):
    """HTML GET handler.
    
    Renders a response to a GET. Queries monsters to feature and renders
    them to the index.html template. Does not accept any query parameters"""
    
    template_values = {
      'monsters' : Monster.all().order('-creation_time').fetch(10)
    }
   
    template = jinja_environment.get_template('index.html')
    self.response.write(template.render(template_values))


class CreatePage(webapp2.RequestHandler):
  """Renders the create page.
  
  Using a MonsterBuilder implementation, it renders the fields for that builder
  and passes the values to the same view via POST, which creates the monster
  and redirects to a view of that monster.
  
  Templates used: create.html"""
  
  def get(self):
    """HTML GET handler.
    
    Renders a form for inputing the information used to create a monster under
    a specific set of rules. The rules are specified by the MonsterBuilder 
    being used."""
    user = users.get_current_user()

    if user:
      template_values = {
        'questions' : CoreMonsterBuilder.questions()
      }
    
      template = jinja_environment.get_template('create.html')
      self.response.write(template.render(template_values))
    else:
      self.redirect(users.create_login_url(self.request.uri))
  
  def answer(self, question, context=""):
    """Helper method to retrieve the answer to a question.
    
    Given a question object with correct metadata, check the request for a
    matching parameter. If present, apply the answer and check for answers
    to any subquestions."""
    
    if hasattr(question, "expectsMultiple"):
      for optionorder, option in enumerate(question.options.values()):
        userinput = cgi.escape(
          self.request.get(context+str(question.order)+"."+str(optionorder)))
        if userinput:
          question(self.___builder, option.value)
          for subquestion in option.subquestions.values():
            self.answer(subquestion, 
              context+str(question.order)+"."+str(optionorder)+"-")
    elif hasattr(question, "expectsOne"):
      userinput = cgi.escape(self.request.get(context+str(question.order)))
      if userinput:
        key = question.options.keys()[int(userinput)]
        question(self.___builder, question.options[key].value)
        # TODO: Handle subquestions
    else:
      question(self.___builder, 
        cgi.escape(self.request.get(context+str(question.order))))
  
  def post(self):
    """HTML POST handler.
    
    POSTS to this page are monster creation requests. Using the request
    parameters, call the handler for each answered question, then redirect to
    the view page for the newly created monster."""
    user = users.get_current_user()

    if user:
      self.___builder = CoreMonsterBuilder()
      for question in CoreMonsterBuilder.questions():
        self.answer(question)
    
      monster = self.___builder.Build()
      creator = Profile.all().filter('account = ',user).get()
      if not creator:
        creator = Profile()
        creator.account = user
        creator.put()
      monster.creator = creator
      monster.put()
    
      self.redirect('/view/?'+urllib.urlencode({'id': monster.key().id()}))
    else:
      self.redirect(users.create_login_url(self.request.uri))


class ViewPage(webapp2.RequestHandler):
  """Renders a single monster view page.
  
  Given the ID of a monster to view, query for that monster and display it
  using the standard monster template.
  
  Templates used: view.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be displayed.
    If found, disply that monster using the standard template."""
    
    template_values = {}
    
    if entity_id:
      template_values['monster'] = Monster.get_by_id(int(entity_id))
    else:
      template_values['monster'] = Monster.all().order("-creation_time").get()
    
    user = users.get_current_user()
    if user:
      template_values['user'] = user
    
    template = jinja_environment.get_template('view.html')
    self.response.write(template.render(template_values))

class DeletePage(webapp2.RequestHandler):
  """Deletes a single monster
  
  Given the ID of a monster to delete, query for that monster and delete it
  iff it's owned by the current user.
  
  Templates used: delete.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be displayed.
    If found, disply that monster using the standard template."""
    
    template_values = {}
    
    if entity_id:
      monster = Monster.get_by_id(int(entity_id))
      if monster:
        user = users.get_current_user()
        if monster.creator.account == user:
          monster.delete()
        else:
          template_values['error'] = 401
      else:
        template_values['error'] = 404
    else:
      template_values['error'] = 404
    
    template = jinja_environment.get_template('delete.html')
    self.response.write(template.render(template_values))

# Define the app
app = webapp2.WSGIApplication([webapp2.Route(r'/', handler=MainPage, name='home'),
                              webapp2.Route(r'/create/', handler=CreatePage, name='create'),
                              webapp2.Route(r'/view', handler=ViewPage, name='latest'),
                              webapp2.Route(r'/view/<entity_id:\d+>', handler=ViewPage, name='view'),
                              webapp2.Route(r'/delete/<entity_id:\d+>', handler=DeletePage, name='delete')],
                              debug=True)

