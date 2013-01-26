import os

from werkzeug.wrappers import Response

from jinja2 import Environment, FileSystemLoader

from model import post

def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
    )
    jinja_env.globals.update(globals)

    #jinja_env.update_template_context(context)
    return jinja_env.get_template(template_name).render(context)

def json_since(request, timestamp):
    posts = post.get_posts(since=timestamp)
    out = render_template(template_name="json.tpl", posts=posts)
    return Response(out)

def json_last(request, count):
    posts = post.get_posts(count=count)
    out = render_template(template_name="json.tpl", posts=posts)
    return Response(out)

def default(request):
    return Response('lol')
