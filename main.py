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
import handlers.home, handlers.create, handlers.view, handlers.edit, handlers.auth, handlers.profile, handlers.delete
import configuration.site

configuration.site.jinja_environment = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

# Define the app
app = webapp2.WSGIApplication([webapp2.Route(r'/', handler=handlers.home.HomeHandler, name='home'),
                              webapp2.Route(r'/create', handler=handlers.create.CreateHandler, name='create'),
                              webapp2.Route(r'/view', handler=handlers.view.ViewHandler, name='latest'),
                              webapp2.Route(r'/view/<entity_id:\d+>', handler=handlers.view.ViewHandler, name='view'),
                              webapp2.Route(r'/edit/<entity_id:\d+>', handler=handlers.edit.EditHandler, name='edit'),
                              webapp2.Route(r'/login', handler=handlers.auth.LoginHandler, name='login'),
                              webapp2.Route(r'/logout', handler=handlers.auth.LogoutHandler, name='logout'),
                              webapp2.Route(r'/profile/edit', handler=handlers.auth.SetupHandler, name='profile.edit'),
                              webapp2.Route(r'/profile', handler=handlers.profile.ProfileHandler, name='profile.me'),
                              webapp2.Route(r'/profile/<profile_id:\d+>', handler=handlers.profile.ProfileHandler, name='profile'),
                              webapp2.Route(r'/delete/<entity_id:\d+>', handler=handlers.delete.DeleteHandler, name='delete')],
                              debug=True)

