import webapp2
from google.appengine.api import users
from monsterrules.common import Profile

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