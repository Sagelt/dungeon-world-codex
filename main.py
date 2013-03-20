#!/usr/bin/env python
#
# Copyright 20013 Sage LaTorra
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2
import os
import handlers.home
import handlers.auth
import handlers.profile
import handlers.search
import handlers.monster
import handlers.product
import handlers.update
import configuration.site

configuration.site.jinja_environment = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

# Define the app
app = webapp2.WSGIApplication([
  webapp2.Route(r'/', handler=handlers.home.HomeHandler, name='home'),
  webapp2.Route(r'/monster', handler=handlers.monster.LandingHandler, name='monster'),
  webapp2.Route(r'/monster/all', handler=handlers.monster.AllHandler, name='monster.all'),
  webapp2.Route(
    r'/monster/create', 
    handler=handlers.monster.CreateHandler, 
    name='monster.create'),
  webapp2.Route(
    r'/monster/<entity_id:[\d\w%]+>', 
    handler=handlers.monster.ViewHandler, 
    name='monster'),
  webapp2.Route(
    r'/monster/<entity_id:[\d\w%]+>/edit', 
    handler=handlers.monster.EditHandler, 
    name='monster.edit'),
  webapp2.Route(
    r'/monster/<entity_id:[\d\w%]+>/delete', 
    handler=handlers.monster.DeleteHandler, 
    name='monster.delete'),
  webapp2.Route(
    r'/monster/<entity_id:[\d\w%]+>/upvote', 
    handler=handlers.monster.UpVoteHandler, 
    name='monster.upvote'),
  webapp2.Route(
    r'/monster/<entity_id:[\d\w%]+>/downvote', 
    handler=handlers.monster.DownVoteHandler, 
    name='monster.downvote'),
  webapp2.Route(r'/login', handler=handlers.auth.LoginHandler, name='login'),
  webapp2.Route(r'/logout', handler=handlers.auth.LogoutHandler, name='logout'),
  webapp2.Route(r'/profile/edit', handler=handlers.profile.EditHandler, name='profile.edit'),
  webapp2.Route(r'/profile', handler=handlers.profile.ProfileHandler, name='profile.me'),
  webapp2.Route(
    r'/profile/<profile_id:[\d\w%]+>', 
    handler=handlers.profile.ProfileHandler, 
    name='profile'),
  webapp2.Route(
    r'/profile/<profile_id:[\d\w%]+>/favorites', 
    handler=handlers.profile.FavoritesHandler, 
    name='favorites'),
  webapp2.Route(
    r'/profile/add/<access_code:[\d\w%]+>', 
    handler=handlers.profile.AddAccessHandler, 
    name='profile.add'),
  webapp2.Route(r'/product/create', handler=handlers.product.CreateHandler, name='product.create'),
  webapp2.Route(r'/product/upload', handler=handlers.product.UploadHandler, name='product.upload'),
  webapp2.Route(
    r'/product/<entity_id:[\d\w%]+>', 
    handler=handlers.product.ViewHandler, 
    name='product'),
  webapp2.Route(
    r'/product/<entity_id:[\d\w%]+>/update', 
    handler=handlers.product.UpdateHandler, 
    name='product.update'),
  webapp2.Route(r'/search', handler=handlers.search.SearchHandler, name='search'),
  webapp2.Route(
    r'/publish', 
    handler=handlers.monster.ProductCreateHandler, 
    name='publish')],
  debug=True)

