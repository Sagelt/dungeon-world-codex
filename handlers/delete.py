import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from monsterrules.common import Monster, Profile
from handlers.base import LoggedInRequestHandler
import configuration.site

class DeleteHandler(LoggedInRequestHandler):
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
    
    template = configuration.site.jinja_environment.get_template('delete.html')
    self.response.write(template.render(template_values))

