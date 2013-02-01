#!/usr/bin/python2

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException
from werkzeug.wsgi import SharedDataMiddleware

from sqlalchemy import create_engine

import os

from config import Configuration
import views
import model

Configuration().load_from_file("wurstgulasch.cfg")

class Wurstgulasch:
    def __init__(self, database_uri):
        # init sqlalchemy
        self.db = create_engine(Configuration().database_uri)
        from sqlalchemy.orm import sessionmaker
        model.Session = sessionmaker(bind=self.db)
 
        # set routing for app
        self.url_map = Map(
            [
                Rule('/', endpoint='default'),
                Rule('/human/view/page/<page>', endpoint='web_view_posts'),
                Rule('/human/view/tags/<tagstr>', endpoint='web_view_posts_tag'),
                Rule('/human/posts/add', endpoint='web_insert_post'),
                Rule('/human/friends/view', endpoint='web_view_friends'),
                Rule('/human/friends/add', endpoint='web_add_friends'),
                Rule('/machine/since/<timestamp>', endpoint='json_since'),
                Rule('/machine/last/<count>', endpoint='json_last')
            ]
        )

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)

        endpoint, values = adapter.match()
        return getattr(views, endpoint)(request, **values)

    def handle_request(self, environment, start_response):
        request = Request(environment)
        response = self.dispatch_request(request)
        return response(environment, start_response)

    def init_database(self):
        import model
        model.Base.metadata.create_all(bind=self.db)

    def __call__(self, environment, start_response):
        return self.handle_request(environment, start_response)

def create_app():
    app = Wurstgulasch(database_uri=Configuration().database_uri)
    app.__call__ = SharedDataMiddleware(
        app.__call__, { 
            '/assets': './assets'
        }
    )
    return app

def shell_init():
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
