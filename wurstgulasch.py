#!/usr/bin/python2.7


from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException
from werkzeug.wsgi import SharedDataMiddleware

from sqlalchemy import create_engine

from jinja2 import Environment, FileSystemLoader

import os
import time
import json

# debug
# import pdb

from config import Configuration
import views
import model

from beaker.middleware import SessionMiddleware

Configuration().load_from_file("wurstgulasch.cfg")


class Wurstgulasch:
    def __init__(self, database_uri):
        # init sqlalchemy
        self.db = create_engine(Configuration().database_uri)
        from sqlalchemy.orm import sessionmaker
        model.Session = sessionmaker(bind=self.db)

        # set routing for app
        self.routes = [
            ( '/', 'default', 'all' ),
            ( '/logout', 'web_logout', 'all' ),
            ( '/login', 'web_login', 'all' ),
            ( '/<username>', 'web_view_user_posts', 'all'),
            ( '/<username>/add', 'web_insert_post', 'all'),
            ( '/<username>/page/<page>', 'web_view_user_posts', 'all'),
            ( '/<username>/json/since/<timestamp>', 'json_since', 'all'),
            ( '/<username>/json/last/<count>', 'json_last', 'all' ),
            ( '/<username>/create', 'web_insert_post', 'user' ),
            ( '/<username>/stream', 'web_view_stream', 'user' ),
            ( '/<username>/stream/tag/<tagstr>', 'web_view_stream_tag', 'user' ),
            ( '/<username>/stream/tag/<tagstr>/page/<page>', 'web_view_stream_tag', 'user' ),
            ( '/<username>/stream/page/<page>', 'web_view_stream', 'user' ),
            ( '/<username>/friends', 'web_view_friends', 'user' ),
            ( '/<username>/friends/add', 'web_add_friends', 'user' ),
            ( '/<username>/friends/delete', 'web_delete_friends', 'user' ),
            ( '/<username>/profile', 'web_view_profile', 'all' ),
            ( '/<username>/profile/change', 'web_change_profile', 'user'),
        ]
        self.url_map = Map(
            [ Rule(x[0], endpoint=x[1]) for x in self.routes]
        )
        
        # set up templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
        )

    def render_template(self, template_name, **context):
        return self.jinja_env.get_template(template_name).render(context)
         
    def query_friends(self):
        from urllib import urlopen
        session = model.Session()
        users = session.query(model.user).all()
        for user in users:
            for friend in user.friends:
                if friend.lastupdated != 0:
                    url = friend.url+"/json/since/"+str(friend.lastupdated)
                else:
                    url = friend.url+"/json/last/100"
                import pdb
                pdb.set_trace()
                file = urlopen(url)
                dicts = json.load(file)
                for p in dicts:
                    # hacketihack
                    try:
                        tmp = model.post(
                            post_id = p['post_id'],
                            timestamp = p['timestamp'],
                            origin = p['origin'],
                            content_type = p['content_type'],
                            content_string = p['content_string'],
                            source = p['source'],
                            description = p['description'],
                            tags = []
                            # reference = p['reference'],
                            # signature = p['signature'],
                        )
                        
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
        
        view = getattr(views, endpoint)
        objs = view(request, environment, **values)
        
        # determine username
        try:
            username = session['username']
        except KeyError, e:
            username = "guest"

        

        out = Response(self.render_template(template_name=endpoint+'.htmljinja', username=username, **objs), mimetype='text/html')
     
        return out


    def handle_request(self, environment, start_response):
        request = Request(environment)
        response = self.dispatch_request(environment, request)
        return response(environment, start_response)

    def init_database(self):
        import model
        model.Base.metadata.create_all(bind=self.db)
        
        from sqlalchemy.orm import sessionmaker
        session = sessionmaker(bind=self.db)()
        
        testuser = model.user(name='testuser', passwordhash='testpassword', tagline='I am only here because I need to be.', bio='I often live short and very exciting lives.')
        session.add(testuser)
        session.commit() 
        
    def __call__(self, environment, start_response):
        return self.handle_request(environment, start_response)

def create_app():
    app = Wurstgulasch(database_uri=Configuration().database_uri)
    app.__call__ = SharedDataMiddleware(
        app.__call__, { 
            '/assets': './assets',
            '/static': './static'
        }
    )
    app.__call__ = SessionMiddleware(app.__call__) 

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
