import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from monsterrules.common import Monster, Profile, Vote
import handlers.base 
import configuration.site

class VoteHandler(webapp2.RequestHandler):
  """Handles +1 of a monster.
  
  If the user has not already +1d a monster, +1 it.
  Otherwise, un-+1 it."""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check if the user has already voted. If they haven't, +1 the monster.
    Otherwise, un-vote."""
    
    monster = Monster.get_by_id(int(entity_id))
    user = users.get_current_user()
    profile = Profile.all().filter("account = ", user).get()
    
    if (not monster) or (not profile):
      self.response.set_status(404)
      return
      
    previous_vote = Vote.all().filter("voter = ", profile).filter("monster = ",monster).get()
    if previous_vote:
      previous_vote.delete()
    else:
      vote = Vote()
      vote.voter = profile
      vote.monster = monster
      vote.put()
    
    monster.put()
    profile.put()
      
    
    
    