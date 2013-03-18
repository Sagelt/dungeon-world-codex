import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile, Vote, Product
import handlers.base
import configuration.site
import xml.etree.ElementTree as ET
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

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


class UpdateHandler(handlers.base.LoggedInRequestHandler):
  """Updates the access code for a product.
  
  Given the ID of a product to update, generate a new access code for it, then redirect to
  the profile edit page."""
  
  def get(self, entity_id=None):
    """HTML GET handler.
    
    Update the product with the specified ID"""
    
    template_values = self.build_template_values()
    
    if entity_id:
      try:
        product = Product.get_by_id(int(entity_id))
      except ValueError:
        return self.not_found()
      if not product:
        self.not_found()
        return
      product.generate_access_code()
      product.put()
    else:
      self.redirect(self.uri_for('product.home'))
      return
    
    return self.redirect(self.uri_for('profile.edit'))


class UploadHandler(handlers.base.LoggedInRequestHandler, blobstore_handlers.BlobstoreUploadHandler):
  """"Uploads a file and parses it for monsters.

  Templates used: upload.html"""

  def get(self):
    """HTML GET handler.

    Check the query parameters for the ID of the monster to be edited.
    If found, display that monster for editing."""

    template_values = self.build_template_values()

    if not template_values[handlers.base.PROFILE_KEY].is_publisher:
      return self.forbidden()

    template_values['products'] = template_values[handlers.base.PROFILE_KEY].get_products()
    template_values['upload_url'] = blobstore.create_upload_url(self.uri_for('product.upload'))

    template = configuration.site.jinja_environment.get_template('product/upload.html')
    self.response.write(template.render(template_values))

  def post(self):
    """HTML POST handler. 

    Parse ALL THE MONSTERS."""

    template_values = self.build_template_values()

    if not template_values[handlers.base.PROFILE_KEY].is_publisher:
      return self.forbidden()

    upload_files = self.get_uploads('file_upload')
    blob_info = upload_files[0]
    blob_key = blob_info.key()
    blob_reader = blobstore.BlobReader(blob_key)
    root = ET.parse(blob_reader)
    
    product = int(self.request.get('product'))
    
    for upload_monster in root.iter('monster'):
      monster = Monster()
      
      monster.product = product
      monster.creator = template_values[handlers.base.PROFILE_KEY]
      
      monster.name = upload_monster.findtext('name')
      
      monster.description = upload_monster.findtext('description')
      
      monster.instinct = upload_monster.findtext('instinct')
      
      tags = upload_monster.find('tags')
      if tags:
        for tag in tags:
          if tag:
            monster.tags.append(tag.text)
        
      monster.damage = upload_monster.findtext('damage')
      
      monster.hp = upload_monster.findtext('hp')
      
      monster.armor = upload_monster.findtext('armor')
      
      damage_tags = upload_monster.find('damage_tags')
      if damage_tags:
        for tag in damage_tags:
          monster.damage_tags.append(tag.text)
      
      special_qualities = upload_monster.find('special_qualities')
      if special_qualities: 
        for special_quality in special_qualities:
          monster.special_qualities.append(special_quality.text)
        
      for move in upload_monster.find('moves'):
        monster.moves.append(move.text)
      
      try:  
        monster.put()
      except:
        print monster
        raise
    
    self.redirect(self.uri_for('product', entity_id=product))
    