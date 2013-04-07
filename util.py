import os
from hashlib import md5

from PIL import Image

from config import Configuration

from werkzeug.wrappers import Response

"""
Checks whether the given mimetype is supported
"""
def check_mimetype(mimetype, supported_maintypes, supported_subtypes):
    mimesplit = mimetype.split('/')
    if mimesplit[0] not in supported_maintypes or mimesplit[1] not in supported_subtypes:
        raise Exception("Unsupported mimetype: " + mimetype + ", expected " + supported_maintypes +
                "/" + supported_subtypes)
    return mimesplit[1]


"""
Generates a thumbnail from a given image with the given width.
The image's aspect ratio will be kept.
"""
def generate_thumbnail(image, width):
    image = image.copy()
    hsize = int(image.size[1] * (width / float(image.size[0])))
    image.thumbnail((width, hsize), Image.ANTIALIAS)
    return image

"""
Forces quadratic geometry on an image
"""
def force_quadratic(image):
    (width, height) = image.size
    if width == height:
        return image
    size = min(width, height)
    delta = (max(width, height)-size)/2
    if width < height:
        box = (0, delta, size, size+delta)
    else:
        box = (delta, 0, size+delta, size)
    image = image.crop(box)
    return image

def get_username(environment):
    """
    gets username from Beaker session in Werkzeug environment. If username is
    not set (which should not be the case, btw!) it returns "guest".
    """
    beaker_session  = environment['beaker.session']
    if 'username' in beaker_session.keys():
        return beaker_session['username']
    else:
        return "guest"

def render_template(template_name, werkzeug_env, mimetype="text/html",  **kwargs):
    """
    renders **kwargs down to the "template_name" in context of 
        werkzeug_env and returns a Werkzeug Response Object
        with the mimetype mime_type which defaults to "text/html"
    """
    jinja_environment = werkzeug_env['jinja_env']
    template = jinja_environment.get_template(template_name)
    username = get_username(werkzeug_env)
    response = Response(template.render(username=username, **kwargs), content_type=mimetype)
    return response
