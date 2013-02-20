import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile, Vote, Product
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


class ProfileHandler(handlers.base.LoggedInRequestHandler):
  """Renders a profile page
  
  Given the ID of a profile to view, query for that profile and display it
  using the standard monster template. If not profile provided, show the 
  current user.
  
  Templates used: profile.html"""
  
  def get(self, profile_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the profile to be displayed.
    If found, display the user. Otherwise display current user"""
    
    template_values = self.build_template_values()
    
    if profile_id and template_values[handlers.base.PROFILE_KEY] and int(profile_id) == template_values[handlers.base.PROFILE_KEY].key().id():
      template_values['viewed_profile'] = template_values[handlers.base.PROFILE_KEY]
    elif profile_id:
      template_values['viewed_profile'] = Profile.get_by_id(int(profile_id))
    elif template_values[handlers.base.PROFILE_KEY]:
      return self.redirect(self.uri_for("profile", profile_id=template_values[handlers.base.PROFILE_KEY].key().id()))
    else:
      return self.forbidden()
      
    template_values['favorites'] = Vote.all().filter("voter = ", template_values[handlers.base.PROFILE_KEY]).fetch(10)
    template_values['monsters'] = Monster.get_most_recent(10, creator=template_values['viewed_profile'], user=template_values[handlers.base.PROFILE_KEY])
    template = configuration.site.jinja_environment.get_template('profile.html')
    return self.response.write(template.render(template_values))
      

class AddAccessHandler(handlers.base.LoggedInRequestHandler):
  """Gives the current user access to the specified product."""
  
  def get(self, access_code=None):
    """HTML GET handler.
    
    Check the query parameters for the access code and grant access to that
    product."""
    
    user = users.get_current_user()
    profile = Profile.for_user(user)
    if not profile:
      return self.forbidden()
    if not access_code:
      return self.forbidden()
      
    product = Product.get_by_access_code(access_code)
    if not product:
      return self.not_found()
      
    profile.products.append(product.key().id())
    profile.put()
    
    return self.redirect(self.uri_for('profile.edit'))
