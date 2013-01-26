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


class LoggedInRequestHandler(webapp2.RequestHandler):
  
  def is_user_logged_in(self):
    self.user = users.get_current_user()
    if self.user:
      self.profile = Profile.all().filter("account = ", self.user).get()
      if self.profile:
        return True
      else:
        self.redirect(self.uri_for('profile.edit'))
    else:
      self.redirect(users.create_login_url(self.request.uri))
      return False

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
      'monsters' : Monster.all().order('-creation_time').fetch(10),
      'user' : users.get_current_user()
    }
   
    template = jinja_environment.get_template('index.html')
    self.response.write(template.render(template_values))


class CreatePage(LoggedInRequestHandler):
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

    if self.is_user_logged_in():
      template_values = {
        'questions' : CoreMonsterBuilder.questions(),
        'user' : self.user
      }
    
      template = jinja_environment.get_template('create.html')
      self.response.write(template.render(template_values))
  
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

    if self.is_user_logged_in():
      self.___builder = CoreMonsterBuilder()
      for question in CoreMonsterBuilder.questions():
        self.answer(question)
    
      monster = self.___builder.Build()
      monster.creator = self.profile
      monster.put()
    
      self.redirect('/view/'+str(monster.key().id()))


class ViewPage(webapp2.RequestHandler):
  """Renders a single monster view page.
  
  Given the ID of a monster to view, query for that monster and display it
  using the standard monster template.
  
  Templates used: view.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be displayed.
    If found, disply that monster using the standard template."""
    
    template_values = {
      'user' : users.get_current_user()
    }
    
    if entity_id:
      template_values['monster'] = Monster.get_by_id(int(entity_id))
    else:
      template_values['monster'] = Monster.all().order("-creation_time").get()
    
    template = jinja_environment.get_template('view.html')
    self.response.write(template.render(template_values))

class DeletePage(LoggedInRequestHandler):
  """Deletes a single monster
  
  Given the ID of a monster to delete, query for that monster and delete it
  iff it's owned by the current user.
  
  Templates used: delete.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be displayed.
    If found, disply that monster using the standard template."""
    
    template_values = {
      'user' : users.get_current_user()
    }
    
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


class EditPage(webapp2.RequestHandler):
  """Edits a single monster
  
  Given the ID of a monster to edit, query for that monster and present it for
  editing iff it's owned by the current user.
  
  Templates used: edit.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be edited.
    If found, display that monster for editing."""
    
    template_values = {
      'user' : users.get_current_user()
    }
    
    if entity_id:
      monster = Monster.get_by_id(int(entity_id))
      if monster:
        user = users.get_current_user()
        if monster.creator.account == user:
          template_values['monster'] = monster
        else:
          template_values['error'] = 401
      else:
        template_values['error'] = 404
    else:
      template_values['error'] = 404
    
    template = jinja_environment.get_template('edit.html')
    self.response.write(template.render(template_values))
    
  def post(self, entity_id=None):
    """HTML POST handler. 
    
    Save changes to the given monster."""
    
    template_values = {
      'user' : users.get_current_user()
    }
    
    if entity_id:
      monster = Monster.get_by_id(int(entity_id))
      if monster:
        user = users.get_current_user()
        if monster.creator.account == user:
          monster.name = self.request.get('name')
          monster.hp = self.request.get('hp')
          monster.armor = self.request.get('armor')
          monster.damage = self.request.get('damage')
          monster.instinct = self.request.get('instinct')
          monster.description = self.request.get('description')
          
          nextindex = 0
          monster.tags = []
          while self.request.get('tag-'+str(nextindex)):
            monster.tags.append(self.request.get('tag-'+str(nextindex)))
            nextindex += 1
          
          nextindex = 0
          monster.special_qualities = []
          while self.request.get('specialquality-'+str(nextindex)):
            monster.special_qualities.append(self.request.get('specialquality-'+str(nextindex)))
            nextindex += 1
          
          nextindex = 0
          monster.damage_tags = []
          while self.request.get('damagetag-'+str(nextindex)):
            monster.damage_tags.append(self.request.get('damagetag-'+str(nextindex)))
            nextindex += 1
            
          nextindex = 0
          monster.moves = []
          while self.request.get('move-'+str(nextindex)):
            monster.moves.append(self.request.get('move-'+str(nextindex)))
            nextindex += 1
          
          monster.edited = True
          monster.put()
          return self.redirect('/view/'+str(monster.key().id()))
        else:
          template_values['error'] = 401
      else:
        template_values['error'] = 404
    else:
      template_values['error'] = 404
      
    template = jinja_environment.get_template('edit.html')
    self.response.write(template.render(template_values))


class LoginPage(LoggedInRequestHandler):
  """Handles user login
  
  If the user is not logged in, direct them to Google login.
  
  If the user is logged in but has no profile, make them set one up.
  
  Otherwise, redirect to home."""
  
  def get(self):
    """HTML GET handler.
    
    Check login status and redirect appropriately."""
    
    if self.is_user_logged_in():
        return self.redirect(self.uri_for('home'))
        

class LogoutPage(webapp2.RequestHandler):
  """Handles user logout
  
  Redirect user to Google logout, then home."""
  
  def get(self):
    """HTML GET handler.
    
    Redirect to logout, then home."""
    
    self.redirect(users.create_logout_url(self.uri_for('home')))


class SetupPage(webapp2.RequestHandler):
  """Sets up user profile
  
  If user if not logged in, send them to login.
  
  If user is logged in but has no profile, set one up.
  
  Otherwise, redirect to profile page."""
  
  def get(self):
    """HTML GET handler.
    
    If user if not logged in, send them to login.

    If user is logged in but has no profile, set one up.

    Otherwise, redirect to profile page."""
    
    user = users.get_current_user()
    if user:
      template_values = {
        'profile' : Profile.all().filter("account = ", user).get()
      }
      template = jinja_environment.get_template('profile_edit.html')
      self.response.write(template.render(template_values))
    else:
      return self.redirect(users.create_login_url(self.request.uri))
      
  def post(self):
    """HTML POST handler.
    
    Setup profile."""
    user = users.get_current_user()
    if user:
      profile = Profile.all().filter("account = ", user).get()
      if not profile:
        profile = Profile()
      profile.display_name = self.request.get('display_name')
      profile.account = user
      profile.put()
      return self.redirect(self.uri_for('profile.me'))
    else:
      return self.redirect(users.create_login_url(self.request.uri))


class ProfilePage(LoggedInRequestHandler):
  """Renders a profile page
  
  Given the ID of a profile to view, query for that profile and display it
  using the standard monster template. If not profile provided, show the 
  current user.
  
  Templates used: profile.html"""
  
  def get(self, profile_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the profile to be displayed.
    If found, display the user. Otherwise display current user"""
    
    template_values = {
      'user' : users.get_current_user()
    }
    
    if profile_id:
      template_values['profile'] = Profile.get_by_id(int(profile_id))
      template_values['monsters'] = Monster.all().filter("creator = ",template_values['profile']).order('-creation_time').fetch(10)
      template = jinja_environment.get_template('profile.html')
      return self.response.write(template.render(template_values))
    elif self.is_user_logged_in():
      template_values['profile'] = self.profile
      template_values['monsters'] = Monster.all().filter("creator = ",template_values['profile']).order('-creation_time').fetch(10)
      template = jinja_environment.get_template('profile.html')
      return self.response.write(template.render(template_values))
      
      

# Define the app
app = webapp2.WSGIApplication([webapp2.Route(r'/', handler=MainPage, name='home'),
                              webapp2.Route(r'/create', handler=CreatePage, name='create'),
                              webapp2.Route(r'/view', handler=ViewPage, name='latest'),
                              webapp2.Route(r'/view/<entity_id:\d+>', handler=ViewPage, name='view'),
                              webapp2.Route(r'/edit/<entity_id:\d+>', handler=EditPage, name='edit'),
                              webapp2.Route(r'/login', handler=LoginPage, name='create'),
                              webapp2.Route(r'/logout', handler=LogoutPage, name='create'),
                              webapp2.Route(r'/profile/edit', handler=SetupPage, name='profile.edit'),
                              webapp2.Route(r'/profile', handler=ProfilePage, name='profile.me'),
                              webapp2.Route(r'/profile/<profile_id:\d+>', handler=ProfilePage, name='profile'),
                              webapp2.Route(r'/delete/<entity_id:\d+>', handler=DeletePage, name='delete')],
                              debug=True)

