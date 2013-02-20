import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile, Vote
import handlers.base
import configuration.site

class FavoritesHandler(handlers.base.LoggedInRequestHandler):
  """Renders the favorites page.
  
  Retrieves favorited monsters.
  
  Templates used: favorites.html"""
  
  def get(self, profile_id=None):
    """HTML GET handler.
    
    Renders a response to a GET. Queries monsters to feature and renders
    them to the index.html template. Does not accept any query parameters"""
    
    template_values = self.build_template_values()
    
    if profile_id:
      template_values['viewed_profile'] = Profile.get_by_id(int(profile_id))
    elif template_values[handlers.base.USER_KEY]:
      template_values['viewed_profile'] = template_values[handlers.base.PROFILE_KEY]
    else:
      return self.forbidden()
    
    query = db.Query(Vote)
    query.filter("voter = ",template_values['viewed_profile'])
    query.order("-creation_time")
    
    cursor = self.request.get('c')
    
    # If we already have a cursor then there are earlier results
    if cursor:
      template_values["less"] = True
    
    if cursor and self.request.get("prev"):
      template_values["favorites"] = query.fetch(10, end_cursor=cursor)
    elif cursor:
      template_values["favorites"] = query.fetch(10, start_cursor=cursor)
    else:
      template_values["favorites"] = query.fetch(10)
      
    if len(template_values["favorites"]) % 10 != 0:
      template_values["more"] = False
    
    template = configuration.site.jinja_environment.get_template('favorites.html')
    self.response.write(template.render(template_values))