import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile, Vote, Product
import handlers.base
import configuration.site

class EditHandler(handlers.base.LoggedInRequestHandler):
  """Edits a user profile
  
  If user if not logged in, send them to login.
  
  If user is logged in but has no profile, set one up.
  
  Otherwise, redirect to profile page."""
  
  def get(self):
    """HTML GET handler.
    
    If user if not logged in, send them to login.

    If user is logged in but has no profile, set one up.

    Otherwise, redirect to profile page."""
    
    template_values = self.build_template_values()
    if not template_values[handlers.base.PROFILE_KEY]:
      profile = Profile()
      profile.display_name = "A Person With No Name"
      profile.account = template_values[handlers.base.USER_KEY]
      profile.put()
      template_values[handlers.base.PROFILE_KEY] = profile
      template_values['new'] = True
    template = configuration.site.jinja_environment.get_template('profile/edit.html')
    self.response.write(template.render(template_values))
      
  def post(self):
    """HTML POST handler.
    
    Setup profile."""
    user = users.get_current_user()
    if user:
      profile = Profile.for_user(user)
      if not profile:
        profile = Profile()
      profile.display_name = self.request.get('display_name')
      profile.account = user
      profile.put()
      return self.redirect(self.uri_for('profile.me'))
    else:
      return self.redirect(users.create_login_url(self.request.uri))

class FavoritesHandler(handlers.base.LoggedInRequestHandler):
  """Renders the favorites page.
  
  Retrieves favorited monsters.
  
  Templates used: all.html"""
  
  def get(self, profile_id=None):
    """HTML GET handler.
    
    Renders a response to a GET. Queries monsters to feature and renders
    them to the index.html template. Does not accept any query parameters"""
    
    template_values = self.build_template_values()
    skip = int(self.request.get("skip", default_value=0))
    favoriter = Profile.get_by_id(int(profile_id))
    template_values['favoriter'] = favoriter
    template_values['monsters'] = favoriter.get_favorites(
      10,
      user=template_values[handlers.base.PROFILE_KEY],
      skip=skip)
    
    if len(template_values['monsters']) >= 10:
      template_values['next'] = str(self.uri_for('profile.monster.all', profile_id=profile_id))+"?skip="+str(skip+10)
      
    if skip >= 10:
      template_values['prev'] = str(self.uri_for('profile.monster.all', profile_id=profile_id))+"?skip="+str(skip-10)
   
    template = configuration.site.jinja_environment.get_template('monster/all.html')
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
    
    favorites = Vote.all().filter("voter = ", template_values['viewed_profile']).filter("is_up = ", True).fetch(1)
    if favorites:
      template_values['recent_up_monster'] = favorites[0].monster
      
    created =   Monster.get_recent(1, creator=template_values['viewed_profile'], user=template_values[handlers.base.PROFILE_KEY])
    if created:
      template_values['recent_monster'] = created[0]
    template = configuration.site.jinja_environment.get_template('profile/view.html')
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


class AllHandler(handlers.base.LoggedInRequestHandler):
  """Renders the all-monsters view
  
  Retrieves monsters, starting with the most recent."""
  
  def get(self, profile_id=None):
    """HTML GET handler.
    
    Renders a response to a GET. Queries monsters to feature and renders
    them. Easy enough, right?"""
    
    template_values = self.build_template_values()
    skip = int(self.request.get("skip", default_value=0))
    creator = Profile.get_by_id(int(profile_id))
    template_values['creator'] = creator
    template_values['monsters'] = Monster.get_recent(
      10,
      creator=creator,
      user=template_values[handlers.base.PROFILE_KEY],
      skip=skip)
    
    if len(template_values['monsters']) >= 10:
      template_values['next'] = str(self.uri_for('profile.monster.all', profile_id=profile_id))+"?skip="+str(skip+10)
      
    if skip >= 10:
      template_values['prev'] = str(self.uri_for('profile.monster.all', profile_id=profile_id))+"?skip="+str(skip-10)
   
    template = configuration.site.jinja_environment.get_template('monster/all.html')
    self.response.write(template.render(template_values))