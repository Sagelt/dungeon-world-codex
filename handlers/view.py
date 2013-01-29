import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from monsterrules.common import Monster, Profile
import configuration.site

class ViewHandler(webapp2.RequestHandler):
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
    
    template = configuration.site.jinja_environment.get_template('view.html')
    self.response.write(template.render(template_values))