#!/usr/bin/python2.7

from werkzeug import Request
from werkzeug.routing import Map, Rule
from werkzeug.wsgi import SharedDataMiddleware

from sqlalchemy import create_engine

from jinja2 import Environment, FileSystemLoader

import sys
import os
import time
import json

# debug
# import pdb

from config import Configuration
import views
import model

from beaker.middleware import SessionMiddleware


class Wurstgulasch:
    def __init__(self, database_uri):
        # init sqlalchemy
        self.db = create_engine(Configuration().database_uri)
        self.db.echo = True
        from sqlalchemy.orm import sessionmaker
        self.session_factory = sessionmaker(bind=self.db)

        # set routing for app
        self.routes = [
            # janitoring
            ('/', 'default', 'all'),
            ('/logout', 'web_logout', 'all'),
            ('/login', 'web_login', 'all'),
            # user specific
            ('/<username>', 'web_view_user_posts', 'all'),
            ('/<username>/add', 'web_insert_post', 'all'),
            ('/<username>/add/<plugin_str>', 'web_insert_post', 'user'),
            ('/<username>/page/<page>', 'web_view_user_posts', 'all'),
            ('/<username>/json/since/<timestamp>', 'json_since', 'all'),
            ('/<username>/json/last/<count>', 'json_last', 'all'),
            ('/<username>/json/info', 'json_user_info', 'all'),
            ('/<username>/json/repost/<int:post_id>', 'json_repost', 'user'),
            # posts
            ('/<username>/post/<postid>', 'web_view_post_detail', 'user'),
            ('/<username>/post/<int:post_id>/repost', 'web_repost', 'user'),
            ('/<username>/stream/tag/<tagstr>/page/<page>',
                'web_view_stream_tag', 'user'),
            ('/<username>/stream', 'web_view_stream', 'user'),
            ('/<username>/stream/tag/<tagstr>', 'web_view_stream_tag', 'user'),
            ('/<username>/stream/page/<page>', 'web_view_stream', 'user'),
            ('/<username>/friends', 'web_view_friends', 'user'),
            ('/<username>/friends/add', 'web_add_friend', 'user'),
            ('/<username>/friends/delete/<int:friendid>', 'web_delete_friend',
                'user'),
            ('/<username>/profile', 'web_view_profile', 'all'),
            ('/<username>/profile/change', 'web_change_profile', 'user'),
            # admin stuff
            ('/admin/users/create', 'admin_create_user', 'admin'),
            ('/admin/users/view', 'admin_view_users', 'admin'),
            ('/admin/users/resetpassword/<username>',
                'admin_reset_password', 'admin'),
            ('/admin/users/delete/<username>', 'admin_delete_user', 'admin')
        ]
        self.url_map = Map(
            [Rule(x[0], endpoint=x[1]) for x in self.routes]
        )

        # set up templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__),
                                    'templates')),
        )

        # load content plugins
        sys.path.append(Configuration().base_path + '/contenttypes')
        self.content_plugins = {}
        filenames = os.listdir(Configuration().base_path + '/contenttypes')
        for filename in filenames:
            if filename.endswith('.py') and not filename == '__init__.py':
                plugin_name = filename[0:-3]
                plugin = __import__(plugin_name)
                self.content_plugins[plugin_name] = plugin.Plugin

    def render_template(self, template_name, **context):
        return self.jinja_env.get_template(template_name).render(context)

    def query_friends(self):
        from urllib import urlopen
        session = model.Session()
        users = session.query(model.user).all()
        for user in users:
            for friend in user.friends:
                if friend.lastupdated != 0:
                    url = friend.url + "/json/since/" + str(friend.lastupdated)
                else:
                    url = friend.url + "/json/last/100"
                file = urlopen(url)
                dicts = json.load(file)
                for p in dicts:
                    # hacketihack
                    try:
                        tmp = model.post(
                            post_id=p['post_id'],
                            timestamp=p['timestamp'],
                            origin=p['origin'],
                            content_type=p['content_type'],
                            content_string=p['content_string'],
                            source=p['source'],
                            description=p['description'],
                            tags=[]
                            # reference=p['reference'],
                            # signature=p['signature'],
                        )

                        tmp.owner = user

                        # check if tag already exists, if not create it.
                        for t in p['tags']:
                            res = session.query(model.tag).filter(model.tag.tag == t).all()
                            if res:
                                tmp.tags.append(res[0])
                            else:
                                new_tag = model.tag(t)
                                session.add(new_tag)
                                tmp.tags.append(new_tag)

                        session.add(tmp)

                    except KeyError, e:
                        raise e

                friend.lastupdated = int(time.time())
        session.commit()

    def dispatch_request(self, environment, request):
        session = environment['beaker.session']

        adapter = self.url_map.bind_to_environ(request.environ)
        endpoint, values = adapter.match()

        # create sqlalchemy session and bind to environment
        db_session = self.session_factory()
        environment['db_session'] = db_session

        # bind jinja_env to werkzeug environment
        environment['jinja_env'] = self.jinja_env

        # bind plugins to werkzeug environment
        environment['content_plugins'] = self.content_plugins

        view = getattr(views, endpoint)
        result = view(request, environment, db_session, **values)

        return result


    def handle_request(self, environment, start_response):
        request = Request(environment)
        response = self.dispatch_request(environment, request)
        return response(environment, start_response)

    def init_database(self):
        import model
        model.Base.metadata.create_all(bind=self.db)

        from sqlalchemy.orm import sessionmaker
        session = sessionmaker(bind=self.db)()
        adminuser = model.user('admin', 'admin')
        #session.add(adminuser.identity)
        session.add(adminuser)
        session.commit()

    def __call__(self, environment, start_response):
        return self.handle_request(environment, start_response)

def create_app(conf_file_location='wurstgulasch.cfg'):

    Configuration().load_from_file(conf_file_location)

    app = Wurstgulasch(database_uri=Configuration().database_uri)
    app.__call__ = SharedDataMiddleware(
        app.__call__, {
            '/assets': './assets',
            '/static': './static'
        }
    )

    #app.__call__ = CacheMiddleware(app.__call__)
    app.__call__ = SessionMiddleware(app.__call__, type='dbm', data_dir='./sessions')

    return app

def shell_init(conf_file_location='wurstgulasch.cfg'):
    Configuration().load_from_file(conf_file_location)
    import model
    return {
        'wurstgulasch': Wurstgulasch(database_uri=Configuration().database_uri),
        'model': model
    }

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    from werkzeug import script

    action_runserver = script.make_runserver(create_app, use_debugger=True, use_reloader=True)
    action_initdb = lambda: create_app().init_database()
    action_shell = script.make_shell(shell_init)

    script.run()
