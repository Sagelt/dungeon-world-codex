import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from monsterrules.common import Monster, Profile, Vote
import handlers.base
import configuration.site

class ViewHandler(handlers.base.LoggedInRequestHandler):
  """Renders a single monster view page.
  
  Given the ID of a monster to view, query for that monster and display it
  using the standard monster template.
  
  Templates used: view.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be displayed.
    If found, disply that monster using the standard template."""
    
    template_values = self.build_template_values()
    
    if entity_id:
      monster = Monster.get_by_id(int(entity_id))
      if not monster:
        self.not_found()
        return
      template_values['monster'] = monster
    else:
      self.redirect("/view/"+str(Monster.all().order("-creation_time").get().key().id()))
      return
    
    if handlers.base.PROFILE_KEY in template_values:
      template_values['vote'] = Vote.all().filter("monster = ", template_values['monster']).filter("voter = ", template_values[handlers.base.PROFILE_KEY]).get()
    
    
    template_values['edit_url'] = self.uri_for('monster.edit', entity_id=entity_id)
    template_values['delete_url'] = self.uri_for('monster.delete', entity_id=entity_id)
    template_values['profile_url'] = self.uri_for('profile', profile_id=monster.creator.key().id())
    template_values['favorite_url'] = self.uri_for('monster.favorite', entity_id=entity_id)
    
    template = configuration.site.jinja_environment.get_template('view.html')
    self.response.write(template.render(template_values))