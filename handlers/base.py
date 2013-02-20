import webapp2
from google.appengine.api import users
from data.models import Profile
import configuration.site

USER_KEY = "user"
PROFILE_KEY = "profile"
LOGIN_URL_KEY = "login_url"

class LoggedInRequestHandler(webapp2.RequestHandler):
      
  def build_template_values(self):
    template_values = {}
    template_values[USER_KEY] = users.get_current_user()
    if not template_values[USER_KEY]:
      template_values[LOGIN_URL_KEY] = users.create_login_url(self.uri_for('login'))
      template_values[PROFILE_KEY] = None
    else:
      template_values[PROFILE_KEY] = Profile.for_user(template_values[USER_KEY])
    
    common_urls = {}
    common_urls['home_url'] = self.uri_for('home')
    common_urls['create_url'] = self.uri_for('monster.create')
    common_urls['profile_url'] = self.uri_for('profile.me')
    common_urls['login_url'] = self.uri_for('login')
    common_urls['logout_url'] = self.uri_for('logout')
    common_urls['search_url'] = self.uri_for('search')
    common_urls['product_create_url'] = self.uri_for('product.create')
    template_values['common_urls'] = common_urls
    
    format_urls = {}
    format_urls['monster_url'] = self.uri_for('monster', entity_id=r'%d')
    format_urls['monster.edit_url'] = self.uri_for('monster.edit', entity_id=r'%d')
    format_urls['monster.delete_url'] = self.uri_for('monster.delete', entity_id=r'%d')
    format_urls['monster.favorite_url'] = self.uri_for('monster.favorite', entity_id=r'%d')
    format_urls['profile'] = self.uri_for('profile', profile_id=r'%d')
    format_urls['product'] = self.uri_for('product', entity_id=r'%d')
    template_values['format_urls'] = format_urls
    
    self.template_values = template_values
    return template_values
    
  def forbidden(self):
    self.response.set_status(403)
    template = configuration.site.jinja_environment.get_template('errors/forbidden.html')
    self.response.write(template.render(self.template_values))
    
  def not_found(self):
    self.response.set_status(404)
    template = configuration.site.jinja_environment.get_template('errors/not_found.html')
    self.response.write(template.render(self.template_values))