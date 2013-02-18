import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from monsterrules.common import Monster, Profile
import handlers.base 
import configuration.site

class LoginHandler(handlers.base.LoggedInRequestHandler):
  """Handles user login
  
  If the user is not logged in, direct them to Google login.
  
  If the user is logged in but has no profile, make them set one up.
  
  Otherwise, redirect to home."""
  
  def get(self):
    """HTML GET handler.
    
    Check login status and redirect appropriately."""
    
    user = users.get_current_user()
    if user:
      profile = Profile.all().filter("account = ", user).get()
      if profile:
        self.redirect(self.uri_for('home'))
      else:
        self.redirect(self.uri_for('profile.edit'))
    else:
      self.redirect(users.create_login_url(self.uri_for('login')))
        

class LogoutHandler(webapp2.RequestHandler):
  """Handles user logout
  
  Redirect user to Google logout, then home."""
  
  def get(self):
    """HTML GET handler.
    
    Redirect to logout, then home."""
    
    self.redirect(users.create_logout_url(self.uri_for('home')))


class SetupHandler(handlers.base.LoggedInRequestHandler):
  """Sets up user profile
  
  If user if not logged in, send them to login.
  
  If user is logged in but has no profile, set one up.
  
  Otherwise, redirect to profile page."""
  
  def get(self):
    """HTML GET handler.
    
    If user if not logged in, send them to login.

    If user is logged in but has no profile, set one up.

    Otherwise, redirect to profile page."""
    
    template_values = self.build_template_values()
    template = configuration.site.jinja_environment.get_template('profile_edit.html')
    self.response.write(template.render(template_values))
      
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
