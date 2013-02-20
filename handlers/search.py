import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users
from data.models import Monster, Profile, _MONSTER_INDEX
import handlers.base
import configuration.site
import cgi
from google.appengine.api import search

class SearchHandler(handlers.base.LoggedInRequestHandler):
  """Renders the search page.
  
  Retrieves monsters from the index based on the query.
  
  Templates used: search.html"""
  
  def get(self):
    """HTML GET handler.
    
    Renders a response to a GET. Queries monsters to feature and renders
    them to the index.html template. Does not accept any query parameters"""
    
    template_values = self.build_template_values()
    query = cgi.escape(self.request.get('q'))
    if query:
      raw_results = search.Index(name=_MONSTER_INDEX).search(query)
      template_values['results'] = []
      for result in raw_results:
        template_values['results'].append(Monster.get_by_id(int(result.doc_id)))
   
    template = configuration.site.jinja_environment.get_template('search.html')
    self.response.write(template.render(template_values))