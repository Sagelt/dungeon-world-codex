import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile
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
      profile = Profile.for_user(user)
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
