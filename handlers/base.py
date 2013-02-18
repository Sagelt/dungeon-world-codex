import webapp2
from google.appengine.api import users
from monsterrules.common import Profile

USER_KEY = "user"
PROFILE_KEY = "profile"
LOGIN_URL_KEY = "login_url"

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
      
  def build_template_values(self):
    template_values = {}
    template_values[USER_KEY] = users.get_current_user()
    if not template_values[USER_KEY]:
      template_values[LOGIN_URL_KEY] = users.create_login_url(self.uri_for('login'))
    else:
      template_values[PROFILE_KEY] = Profile.all().filter("account = ", template_values[USER_KEY]).get()
    return template_values
    