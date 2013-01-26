from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException

import views

class Wurstgulasch:
    def __init__(self):
        self.url_map = Map(
            [
                Rule('/', endpoint='default'),
                Rule('/machine/since/<timestamp>', endpoint='json_since'),
                Rule('/machine/last/<count>', endpoint='json_last')
            ]
        )

    def default(request):
        return Response('asdf')

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(views, endpoint)(request, **values)
        except HTTPException,e:
            pass

    def handle_request(self, environment, start_response):
        request = Request(environment)
        response = self.dispatch_request(request)
        return response(environment, start_response)

    def __call__(self, environment, start_response):
        return self.handle_request(environment, start_response)

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, Wurstgulasch(), use_debugger=False) 
