import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from monsterrules.common import Monster, Profile
import configuration.site

class HomeHandler(webapp2.RequestHandler):
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
   
    template = configuration.site.jinja_environment.get_template('index.html')
    self.response.write(template.render(template_values))