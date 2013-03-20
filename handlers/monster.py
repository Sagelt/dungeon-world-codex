import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile, Vote, Product
from monsterrules.core.builder import CoreMonsterBuilder
import handlers.base 
import configuration.site
import cgi


class CreateHandler(handlers.base.LoggedInRequestHandler):
  """Renders the create page.
  
  Using a MonsterBuilder implementation, it renders the fields for that builder
  and passes the values to the same view via POST, which creates the monster
  and redirects to a view of that monster.
  
  Templates used: create.html"""
  
  def get(self):
    """HTML GET handler.
    
    Renders a form for inputing the information used to create a monster under
    a specific set of rules. The rules are specified by the MonsterBuilder 
    being used."""
    
    template_values = self.build_template_values()
    template_values['questions']= CoreMonsterBuilder.questions()
    
    product = self.request.get('product')
    if product:
      product = Product.get_by_id(int(product))
      if product.creator.account != template_values[handlers.base.USER_KEY]:
        return self.forbidden()
      template_values['product'] = product
    
    template = configuration.site.jinja_environment.get_template('monster/create.html')
    self.response.write(template.render(template_values))
  
  def answer(self, question, context=""):
    """Helper method to retrieve the answer to a question.
    
    Given a question object with correct metadata, check the request for a
    matching parameter. If present, apply the answer and check for answers
    to any subquestions."""
    
    if hasattr(question, "expectsMultiple"):
      for optionorder, option in enumerate(question.options.values()):
        userinput = cgi.escape(
          self.request.get(context+str(question.order)+"."+str(optionorder)))
        if userinput:
          question(self.___builder, option.value)
          for subquestion in option.subquestions.values():
            self.answer(subquestion, 
              context+str(question.order)+"."+str(optionorder)+"-")
    elif hasattr(question, "expectsOne"):
      userinput = cgi.escape(self.request.get(context+str(question.order)))
      if userinput:
        key = question.options.keys()[int(userinput)]
        question(self.___builder, question.options[key].value)
        # TODO: Handle subquestions
    else:
      question(self.___builder, 
        cgi.escape(self.request.get(context+str(question.order))))
  
  def post(self):
    """HTML POST handler.
    
    POSTS to this page are monster creation requests. Using the request
    parameters, call the handler for each answered question, then redirect to
    the view page for the newly created monster."""

    template_values = self.build_template_values()
    if template_values[handlers.base.PROFILE_KEY]:
      self.___builder = CoreMonsterBuilder()
      for question in CoreMonsterBuilder.questions():
        self.answer(question)
    
      monster = self.___builder.Build()
      monster.creator = template_values[handlers.base.PROFILE_KEY]
      
      product = self.request.get('product')
      if product:
        monster.product = int(product)
        
      license = self.request.get('license')
      if license:
        monster.license = configuration.site.licenses[license]
      
      monster.put()
      self.redirect(self.uri_for("monster", entity_id=monster.key().id()))
    else:
      self.forbidden()


class DeleteHandler(handlers.base.LoggedInRequestHandler):
  """Deletes a single monster
  
  Given the ID of a monster to delete, query for that monster and delete it
  iff it's owned by the current user.
  
  Templates used: delete.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be displayed.
    If found, disply that monster using the standard template."""
    
    template_values = self.build_template_values()
    
    if entity_id:
      monster = Monster.get_by_id_safe(int(entity_id), template_values[handlers.base.PROFILE_KEY])
      if monster:
        if monster.creator.account == template_values[handlers.base.USER_KEY]:
          monster.delete()
        else:
          return self.forbidden()
      else:
        return self.not_found()
    else:
      return self.not_found()
    
    template = configuration.site.jinja_environment.get_template('monster/delete.html')
    self.response.write(template.render(template_values))


class EditHandler(handlers.base.LoggedInRequestHandler):
  """Edits a single monster
  
  Given the ID of a monster to edit, query for that monster and present it for
  editing iff it's owned by the current user.
  
  Templates used: edit.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be edited.
    If found, display that monster for editing."""
    
    template_values = self.build_template_values()
    
    if entity_id:
      monster = Monster.get_by_id_safe(int(entity_id), template_values[handlers.base.PROFILE_KEY])
      if monster:
        if monster.creator.account == template_values[handlers.base.USER_KEY]:
          template_values['monster'] = monster
          template_values['delete_url'] = self.uri_for('monster.delete', entity_id=entity_id)
        else:
          return self.forbidden()
      else:
        return self.not_found()
    else:
      return self.not_found()
    
    template = configuration.site.jinja_environment.get_template('monster/edit.html')
    self.response.write(template.render(template_values))
    
  def post(self, entity_id=None):
    """HTML POST handler. 
    
    Save changes to the given monster."""
    
    template_values = self.build_template_values()
    
    if entity_id:
      monster = Monster.get_by_id_safe(int(entity_id), template_values[handlers.base.PROFILE_KEY])
      if monster:
        user = users.get_current_user()
        if monster.creator.account == user:
          monster.name = self.request.get('name')
          monster.hp = self.request.get('hp')
          monster.armor = self.request.get('armor')
          monster.damage = self.request.get('damage')
          monster.instinct = self.request.get('instinct')
          monster.description = self.request.get('description')
          
          nextindex = 0
          monster.tags = []
          while self.request.get('tag-'+str(nextindex)):
            monster.tags.append(self.request.get('tag-'+str(nextindex)))
            nextindex += 1
          
          nextindex = 0
          monster.special_qualities = []
          while self.request.get('specialquality-'+str(nextindex)):
            monster.special_qualities.append(self.request.get('specialquality-'+str(nextindex)))
            nextindex += 1
          
          nextindex = 0
          monster.damage_tags = []
          while self.request.get('damagetag-'+str(nextindex)):
            monster.damage_tags.append(self.request.get('damagetag-'+str(nextindex)))
            nextindex += 1
            
          nextindex = 0
          monster.moves = []
          while self.request.get('move-'+str(nextindex)):
            monster.moves.append(self.request.get('move-'+str(nextindex)))
            nextindex += 1
          
          monster.edited = True
          monster.put()
          return self.redirect(self.uri_for("monster", entity_id=monster.key().id()))
        else:
          return self.forbidden()
      else:
        return self.not_found()
    else:
      return self.not_found()
      
    template = configuration.site.jinja_environment.get_template('monster/edit.html')
    self.response.write(template.render(template_values))

class LandingHandler(handlers.base.LoggedInRequestHandler):
  """A landing page for monsters.
  
  If the user comes to a monster url without an id, just show this."""
  
  def get(self):
    """HTML GET handler.
    
    Just show a template with the normal template values."""
    
    template_values = self.build_template_values()
    template_values['monsters'] = Monster.get_most_recent(10, user=template_values[handlers.base.PROFILE_KEY])
    
    template = configuration.site.jinja_environment.get_template('monster/landing.html')
    self.response.write(template.render(template_values))

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
      try:
        monster = Monster.get_by_id_safe(int(entity_id), template_values[handlers.base.PROFILE_KEY])
      except ValueError:
        return self.not_found()
      if not monster:
        self.not_found()
        return
      template_values['monster'] = monster
    else:
      self.redirect("/view/"+str(Monster.all().order("-creation_time").get().key().id()))
      return
    
    if handlers.base.PROFILE_KEY in template_values:
      template_values['vote'] = Vote.all().filter("monster = ", template_values['monster']).filter("voter = ", template_values[handlers.base.PROFILE_KEY]).get()
    
    template_values['edit_url'] = self.uri_for('monster.edit', entity_id=r'%s')
    template_values['delete_url'] = self.uri_for('monster.delete', entity_id=entity_id)
    template_values['profile_url'] = self.uri_for('profile', profile_id=monster.creator.key().id())
    
    template = configuration.site.jinja_environment.get_template('monster/view.html')
    self.response.write(template.render(template_values))


class UpVoteHandler(webapp2.RequestHandler):
  """Handles +1 of a monster.
  
  If the user has not already +1d a monster, do nothing. Otherwise, +1 that sucker."""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check if the user has already voted. If they haven't, +1 the monster.
    Otherwise, error."""
    
    user = users.get_current_user()
    profile = Profile.all().filter("account = ", user).get()
    monster = Monster.get_by_id_safe(int(entity_id), profile)
    
    if (not monster) or (not profile):
      return self.forbidden()
      
    previous_vote = Vote.all().filter("voter = ", profile).filter("monster = ",monster).get()
    if previous_vote and previous_vote.is_up:
      return self.response.set_status(500)
    elif previous_vote:
      previous_vote.is_up = True
      previous_vote.put()
      
      if monster.downs:
        monster.downs -= 1
      else:
        monster.downs = 0
        
      if monster.ups:
        monster.ups += 1
      else:
        monster.ups = 1
      
      monster.compute_score()
      monster.put()
    else:
      vote = Vote()
      vote.voter = profile
      vote.monster = monster
      vote.put()
      
      if monster.ups:
        monster.ups += 1
      else:
        monster.ups = 1
      monster.compute_score()
      monster.put()


class DownVoteHandler(webapp2.RequestHandler):
  """Handles -1 of a monster.
  
  If the user has not already -1d a monster, do nothing. Otherwise, -1 that sucker."""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check if the user has already voted. If they haven't, -1 the monster.
    Otherwise, error."""
    
    user = users.get_current_user()
    profile = Profile.all().filter("account = ", user).get()
    monster = Monster.get_by_id_safe(int(entity_id), profile)
    
    if (not monster) or (not profile):
      return self.forbidden()
      
    previous_vote = Vote.all().filter("voter = ", profile).filter("monster = ",monster).get()
    if previous_vote and previous_vote.is_up:
      previous_vote.is_up = False
      previous_vote.put()
      
      if monster.downs:
        monster.downs += 1
      else:
        monster.downs = 1
        
      if monster.ups:
        monster.ups -= 1
      else:
        monster.ups = 0
        
      monster.compute_score()
      monster.put()
    elif previous_vote:
      return self.response_set_status(500)
    else:
      vote = Vote()
      vote.voter = profile
      vote.monster = monster
      vote.is_up = False
      vote.put()
      
      if monster.downs:
        monster.downs += 1
      else:
        monster.downs = 1
      monster.compute_score()
      monster.put()


class ProductCreateHandler(handlers.base.LoggedInRequestHandler):
  """"Creates a single monster that's part of a product
  
  Templates used: edit.html"""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check the query parameters for the ID of the monster to be edited.
    If found, display that monster for editing."""
    
    template_values = self.build_template_values()
    
    if not template_values[handlers.base.PROFILE_KEY].is_publisher:
      return self.forbidden()
      
    template_values['products'] = template_values[handlers.base.PROFILE_KEY].get_products()
    
    template = configuration.site.jinja_environment.get_template('monster/publish.html')
    self.response.write(template.render(template_values))
    
  def post(self, entity_id=None):
    """HTML POST handler. 
    
    Save changes to the given monster."""
    
    template_values = self.build_template_values()
    
    if not template_values[handlers.base.PROFILE_KEY].is_publisher:
      return self.forbidden()
    
    monster = Monster()
    
    monster.product = int(self.request.get('product'))
    monster.creator = template_values[handlers.base.PROFILE_KEY]
    
    if monster.product == -1:
      monster.is_core = True
    
    license = self.request.get('license')
    if license:
      monster.license = configuration.site.licenses[license]
    else:
      return self.error()
    
    name = self.request.get('name')
    if name:
      monster.name = name
    else:
      return self.error()
      
    tags = self.request.get('tags')
    if tags:
      for tag in tags.split(", "):
        monster.tags.append(tag)
    else:
      return self.error()
    
    damage = self.request.get('damage')
    if damage:
      monster.damage = damage
    else:
      return self.error()
    
    hp = self.request.get('hp')
    if hp:
      monster.hp = hp
    else:
      return self.error()
    
    armor = self.request.get('armor')
    if armor:
      monster.armor = armor
    else:
      return self.error()
      
    damage_tags = self.request.get('damage_tags')
    if damage_tags:
      for tag in damage_tags.split(", "):
        monster.damage_tags.append(tag)
    else:
      return self.error()
    
    special_qualities = self.request.get('special_qualities')
    if special_qualities:
      for sq in special_qualities.split(", "):
        monster.special_qualities.append(sq)
    else:
      return self.error()
      
    description = self.request.get('description')
    if armor:
      monster.description = description
    else:
      return self.error()
    
    instinct = self.request.get('instinct')
    if instinct:
      monster.instinct = instinct
    else:
      return self.error()
    
    moves = self.request.get('moves')
    if moves:
      for move in moves.split("\n"):
        monster.moves.append(move)
    else:
      return self.error()
      
    monster.put()
    return self.redirect(self.uri_for("monster", entity_id=monster.key().id()))
    

class AllHandler(handlers.base.LoggedInRequestHandler):
  """Renders the all-monsters view
  
  Retrieves monsters, starting with the most recent."""
  
  def get(self):
    """HTML GET handler.
    
    Renders a response to a GET. Queries monsters to feature and renders
    them. Easy enough, right?"""
    
    template_values = self.build_template_values()
    skip = int(self.request.get("skip", default_value=0))
    template_values['monsters'] = Monster.get_recent_public(skip=skip)
    
    if len(template_values['monsters']) >= 10:
      template_values['next'] = str(self.uri_for('monster.all'))+"?skip="+str(skip+10)
      
    if skip >= 10:
      template_values['prev'] = str(self.uri_for('monster.all'))+"?skip="+str(skip-10)
   
    template = configuration.site.jinja_environment.get_template('monster/all.html')
    self.response.write(template.render(template_values))