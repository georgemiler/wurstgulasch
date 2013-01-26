from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException

import views

class Wurstgulasch:
    def __init__(self):
        self.url_map = Map(
            [
                Rule('/', endpoint='default'),
                Rule('/human/view/<page>', endpoint='web_view_posts'),
                Rule('/human/view', endpoint='web_view_posts'),
                Rule('/human/add', endpoint='web_insert_post'),
                Rule('/machine/since/<timestamp>', endpoint='json_since'),
                Rule('/machine/last/<count>', endpoint='json_last')
            ]
        )

    def default(request):
        return Response('asdf')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)

        endpoint, values = adapter.match()
        return getattr(views, endpoint)(request, **values)

    def handle_request(self, environment, start_response):
        request = Request(environment)
        response = self.dispatch_request(request)
        return response(environment, start_response)

    def __call__(self, environment, start_response):
        return self.handle_request(environment, start_response)

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, Wurstgulasch(), use_debugger=True, use_reloader=True) 
