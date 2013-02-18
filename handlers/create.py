import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from monsterrules.common import Monster, Profile
from monsterrules.core.builder import CoreMonsterBuilder
import handlers.base 
import configuration.site

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
      monster.put_searchable()
      self.redirect('/view/'+str(monster.key().id()))
    else:
      template = configuration.site.jinja_environment.get_template('create.html')
      self.response.write(template.render(template_values))

