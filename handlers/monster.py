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
    
    template = configuration.site.jinja_environment.get_template('create.html')
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
    
    template = configuration.site.jinja_environment.get_template('delete.html')
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
    
    template = configuration.site.jinja_environment.get_template('edit.html')
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
      
    template = configuration.site.jinja_environment.get_template('edit.html')
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
    template_values['favorite_url'] = self.uri_for('monster.favorite', entity_id=entity_id)
    
    template = configuration.site.jinja_environment.get_template('view.html')
    self.response.write(template.render(template_values))


class VoteHandler(webapp2.RequestHandler):
  """Handles +1 of a monster.
  
  If the user has not already +1d a monster, +1 it.
  Otherwise, un-+1 it."""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Check if the user has already voted. If they haven't, +1 the monster.
    Otherwise, un-vote."""
    
    monster = Monster.get_by_id_safe(int(entity_id), template_values[handlers.base.PROFILE_KEY])
    user = users.get_current_user()
    profile = Profile.all().filter("account = ", user).get()
    
    if (not monster) or (not profile):
      return self.forbidden()
      
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