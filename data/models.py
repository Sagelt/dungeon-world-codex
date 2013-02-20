from google.appengine.ext import db
from google.appengine.api import search

class Profile(db.Model):
  account = db.UserProperty()
  display_name = db.StringProperty()
  
  @staticmethod
  def for_user(user):
    return Profile.all().filter("account = ", user).get()


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
  
  def __str__(self):
    return "%s %s %s %s %s %s %s %s %s %s" % (self.name, " ".join(self.tags), 
      self.damage, self.hp, self.armor, " ".join(self.damage_tags), 
      self.instinct, self.description, " ".join(self.special_qualities), 
      " ".join(self.moves))
      
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
        
  def put_unsearchable(self):
    db.Model.put(self)
    
  def put(self):
    db.Model.put(self)
    self.make_searchable()
    
  def delete(self):
    for favorite in Vote.all().filter("monster = ",self).run():
      favorite.delete()
    try:
        search.Index(name=_MONSTER_INDEX).delete(str(self.key().id()))
    except search.Error:
        logging.exception('Delete failed')
    db.Model.delete(self)
   
  @staticmethod 
  def get_most_recent(limit, creator=None):
    query = db.Query(Monster)
    if creator:
      query.filter("creator = ",creator)
    query.order("-creation_time")
    return query.fetch(limit)
    
  @staticmethod
  def search(query):
    raw_results = search.Index(name=_MONSTER_INDEX).search(query)
    return [Monster.get_by_id(int(result.doc_id)) for result in raw_results]
    


class Vote(db.Model):
  voter = db.ReferenceProperty(reference_class=Profile)
  monster = db.ReferenceProperty(reference_class=Monster)
  creation_time = db.DateTimeProperty(auto_now_add=True)