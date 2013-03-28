from google.appengine.ext import db
from google.appengine.api import search
import logging
import uuid
from math import sqrt
import configuration.site
from google.appengine.api import memcache

class Profile(db.Model):
  account = db.UserProperty()
  display_name = db.StringProperty()
  products = db.ListProperty(long, default=[-1])
  is_publisher = db.BooleanProperty(default=False)
  
  @staticmethod
  def for_user(user):
    key = Profile.all().filter("account = ", user).get(keys_only=True)
    if not key:
      return None
    
    mem_key = Profile.get_mem_key_for_id(key.id())
    data = memcache.get(mem_key)
    if not data:
      data = Profile.all().filter("account = ", user).get()
      memcache.add(mem_key, data)
    return data
    
  def get_mem_key(self):
    return Profile.get_mem_key_for_id(self.key().id())
  
  def put(self):
    db.Model.put(self)
    memcache.delete(self.get_mem_key())
    
  def get_products(self):
    result = []
    for product in self.products:
      if product != -1:
        result.append(Product.get_by_id(product))
    return result
    
  def get_published_products(self):
    return Product.all().filter("creator = ", self).fetch(100)
    
  def has_product(self, product):
    return product.key().id() in self.products
    
  def get_favorites(self, limit, skip=0, user=None):
    query = db.Query(Vote)
    query.filter("voter = ",self)
    query.filter("is_up = ",True)
    query.order("-creation_time")
    
    result = []
    for vote in query.run():
      monster = Monster.get_by_id_safe(vote.monster.key().id(), user)
      if monster:
        if skip:
          skip -= 1
        else:
          result.append(monster)
          if len(result) >= limit:
            return result
    return result
  
  @staticmethod
  def get_mem_key_for_id(sid):
    return "profile:%s" % sid
    
  @staticmethod
  def get_by_id_safe(sid, user=None):
    mem_key = Profile.get_mem_key_for_id(sid)
    result = memcache.get(mem_key)
    if not result:
      result = Profile.get_by_id(id)
      memcache.add(mem_key, result)
    if not result:
      return None

    return None


_MONSTER_INDEX = "monsters"

class Monster(db.Model):
  """Model for a Dungeon World monster"""
  
  # Dungeon World Monster Properties
  name = db.StringProperty()
  hp = db.StringProperty()
  armor = db.StringProperty()
  damage = db.StringProperty()
  damage_tags = db.StringListProperty()
  tags = db.StringListProperty()
  special_qualities = db.StringListProperty()
  instinct = db.StringProperty()
  description = db.TextProperty()
  moves = db.StringListProperty()
  
  # Monster Builder Properties
  creator = db.ReferenceProperty(reference_class=Profile)
  creation_time = db.DateTimeProperty(auto_now_add=True)
  creation_rules = db.StringProperty()
  edited = db.BooleanProperty(default=False)
  product = db.IntegerProperty(default=-1)
  license = db.StringProperty()
  is_core = db.BooleanProperty(default=False)
  ups = db.IntegerProperty(default=0)
  downs = db.IntegerProperty(default=0)
  score = db.FloatProperty(default=0.0)
  
  def __str__(self):
    x = " ".join(self.tags)
    return ("%s %s %s %s %s %s %s %s %s %s" % (self.name, " ".join(self.tags), 
      self.damage, self.hp, self.armor, " ".join(self.damage_tags), 
      self.instinct, self.description, " ".join(self.special_qualities), 
      " ".join(self.moves))).encode('utf-8')
      
  def create_document(self):
    return search.Document(
            doc_id=str(self.key().id()), 
            fields=[search.TextField(name='stats', value=str(self))])
            
  def make_searchable(self):
    try:
        search.Index(name=_MONSTER_INDEX).put(self.create_document())
    except search.Error:
        logging.exception('Put failed')
        
  def make_unsearchable(self):
    try:
        search.Index(name=_MONSTER_INDEX).delete(self.key().id())
    except search.Error:
        logging.exception('Delete failed')
  
  def compute_score(self):
    # It's possible these properties might be None. Make sure they're
    # ints instead.
    if not self.ups:
      self.ups = 0
    if not self.downs:
      self.downs = 0
    
    if (self.ups - self.downs) == 0:
      self.score = 0.0
    else:
      n = self.ups + self.downs
      z = 1.0 #1.0 = 85%, 1.6 = 95%
      phat = float(self.ups) / n
      self.score = ((phat + z*z/(2*n) - z * sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n))
      
        
  def put_unsearchable(self):
    db.Model.put(self)
    
  def put(self):
    db.Model.put(self)
    memcache.delete(self.get_mem_key())
    self.make_searchable()
    
  def delete(self):
    for favorite in Vote.all().filter("monster = ",self).run():
      favorite.delete()
    try:
        search.Index(name=_MONSTER_INDEX).delete(str(self.key().id()))
    except AssertionError as e:
      if e.message == 'No api proxy found for service "search"':
        pass
      else:
        raise e
      
    db.Model.delete(self)
    
  def get_product(self):
    mem_key = "product:%s" % self.product
    data = memcache.get(mem_key)
    if not data:
      data = Product.get_by_id(self.product)
      memcache.add(mem_key, data)
    return data
            
  def get_tags(self):
    return ", ".join(self.tags)
    
  def get_damage_tags(self):
    return ", ".join(self.damage_tags)
    
  def get_special_qualities(self):
    return ", ".join(self.special_qualities)
    
  def get_license(self):
    if self.is_core:
      return configuration.site.licenses['Creative Commons Attribution']
    if not hasattr(self, 'license'):
      return "All rights reserved."
    if not self.license:
      return "All rights reserved."
    else:
      return self.license
    
  def url(self):
    return "/monster/"+str(self.key().id())
    
  def vote(self, profile):
    return Vote.all().filter("voter = ", profile).filter("monster = ",self).get()
     
  def get_mem_key(self):
     return "monster:%s" % self.key().id()
   
  @staticmethod 
  def get_recent(limit, creator=None, user=None, skip=0):
    query = db.Query(Monster)
    if creator:
      query.filter("creator = ",creator)
    query.order("-creation_time")
    
    result = []
    for monster_key in query.run(keys_only=True):
      monster = Monster.get_by_id_safe(monster_key.id(), user)
      if monster:
        if skip:
          skip -= 1
        else:
          result.append(monster)
          if len(result) >= limit:
            return result
    return result
      
    
  @staticmethod 
  def get_recent_public(skip=0):
    mem_key = "recent:%s" % skip
    
    data = memcache.get(mem_key)
    if not data:
      query = db.Query(Monster)
      query.filter("product = ",-1)
      query.order("-creation_time")
      data = query.fetch(10, offset=skip)
      memcache.add(mem_key, data, 600)
    return data
  
  @staticmethod 
  def get_top_rated(limit, creator=None, user=None):
    query = db.Query(Monster)
    if creator:
      query.filter("creator = ",creator)
    
    query.order("-score")
    result = []
    for monster_key in query.run(keys_only=True):
      monster = Monster.get_by_id_safe(monster_key.id(), user)
      if monster:
        result.append(monster)
        if len(result) >= limit:
          return result
    return result
    
  @staticmethod
  def search(query, user=None):
    raw_results = search.Index(name=_MONSTER_INDEX).search(query)
    return [Monster.get_by_id_safe(int(result.doc_id), user) for result in raw_results]
    
  @staticmethod
  def get_by_id_safe(id, user=None):
    mem_key = "monster:%s" % id
    result = memcache.get(mem_key)
    if not result:
      result = Monster.get_by_id(id)
    if not result:
      return None
    else:
      memcache.add(mem_key, result)
    if user and (result.product in user.products):
      return result
    elif result.product == -1:
      return result
    
    return None
    


class Vote(db.Model):
  voter = db.ReferenceProperty(reference_class=Profile)
  monster = db.ReferenceProperty(reference_class=Monster)
  creation_time = db.DateTimeProperty(auto_now_add=True)
  is_up = db.BooleanProperty(default=True)
  
  def is_down(self):
    return not self.is_up

class Product(db.Model):
  name = db.StringProperty()
  creator = db.ReferenceProperty(reference_class=Profile)
  access_code = db.StringProperty()
  description = db.TextProperty()
  link = db.LinkProperty()
  
  def generate_access_code(self):
    self.access_code = uuid.uuid4().hex
    
  def get_contents(self):
    return Monster.all().filter("product = ", self.key().id()).fetch(200)
  
  @staticmethod
  def get_by_access_code(code):
    return Product.all().filter("access_code = ", code).get()