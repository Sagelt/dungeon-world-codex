import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile, Vote, Product
import handlers.base
import configuration.site

class CreateHandler(handlers.base.LoggedInRequestHandler):
  """Creates a new product
  
  Given the name of the product, create a new product with the current user as
  the creator and a random access code."""
  
  def get(self):
    """HTML GET handler.
    
    Render a form that has all the data to make a product."""
    
    template_values = self.build_template_values()
    
    if not template_values[handlers.base.PROFILE_KEY]:
      return self.forbidden()
    elif not template_values[handlers.base.PROFILE_KEY].is_publisher:
      return self.forbidden()
      
    template = configuration.site.jinja_environment.get_template('product/create.html')
    self.response.write(template.render(template_values))
  
  def post(self):
    """HTML POST handler.
    
    Check the query parameters for the name of the product, then make it."""
    
    template_values = self.build_template_values()
    
    if not template_values[handlers.base.PROFILE_KEY]:
      return self.forbidden()
    elif not template_values[handlers.base.PROFILE_KEY].is_publisher:
      return self.forbidden()
    
    name = self.request.get('name')
    description = self.request.get('description')
    link = self.request.get('link')
    if (not name) or (not link) or (not description):
      return self.forbidden()
    
    product = Product()
    product.creator = template_values[handlers.base.PROFILE_KEY]
    product.name = name
    product.link = link
    product.description = description
    product.generate_access_code()
    product.put()
    
    template_values[handlers.base.PROFILE_KEY].products.append(product.key().id())
    template_values[handlers.base.PROFILE_KEY].put()
    
    return self.redirect(self.uri_for('profile.edit'))
    

class ViewHandler(handlers.base.LoggedInRequestHandler):
  """Renders a single product view page.
  
  Given the ID of a product to view, query for that prodict and display it
  using the standard product template."""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Display the product with the specified ID"""
    
    template_values = self.build_template_values()
    
    if entity_id:
      try:
        product = Product.get_by_id(int(entity_id))
      except ValueError:
        return self.not_found()
      if not product:
        self.not_found()
        return
      template_values['product'] = product
    else:
      self.redirect(self.uri_for('product.home'))
      return
    
    template = configuration.site.jinja_environment.get_template('product/view.html')
    self.response.write(template.render(template_values))
