import re

from PIL import Image

from werkzeug.wrappers import Response

from wtforms.validators import ValidationError

def check_mimetype(mimetype, supported_maintypes, supported_subtypes):
    """
    Checks whether the given mimetype is supported
    """
    mimesplit = mimetype.split('/')
    if mimesplit[0] not in supported_maintypes or mimesplit[1] not in\
            supported_subtypes:
        raise Exception("Unsupported mimetype: " + mimetype + ",\
                        expected " + supported_maintypes + "/" +
                        supported_subtypes)
    return mimesplit[1]


def generate_thumbnail(image, width):
    """
    Generates a thumbnail from a given image with the given width.
    The image's aspect ratio will be kept.
    """
    image = image.copy()
    hsize = int(image.size[1] * (width / float(image.size[0])))
    image.thumbnail((width, hsize), Image.ANTIALIAS)
    return image


def force_quadratic(image):
    """
    Forces quadratic geometry on an image
    """
    (width, height) = image.size
    if width == height:
        return image
    size = min(width, height)
    delta = (max(width, height) - size) / 2
    if width < height:
        box = (0, delta, size, size + delta)
    else:
        box = (delta, 0, size + delta, size)
    image = image.crop(box)
    return image


def get_username(environment):
    """
    gets username from Beaker session in Werkzeug environment. If username is
    not set (which should not be the case, btw!) it returns "guest".
    """

    beaker_session = environment['beaker.session']
    if 'username' in beaker_session.keys():
        return beaker_session['username']
    else:
        return "guest"


def render_template(template_name, werkzeug_env, mimetype="text/html",
                    **kwargs):
    """
    renders **kwargs down to the "template_name" in context of
        werkzeug_env and returns a Werkzeug Response Object
        with the mimetype mime_type which defaults to "text/html"
    """
    jinja_environment = werkzeug_env['jinja_env']
    template = jinja_environment.get_template(template_name)
    username = get_username(werkzeug_env)
    response = Response(template.render(username=username, **kwargs),
                        content_type=mimetype)
    return response


def escape_html(string):
    string = re.sub('<', '&lt;', string)
    string = re.sub('>', '&gt;', string)
    return string

def tag_validator(form, field):
    tag_str = [t.strip() for t in field.data.split(',')]
    for tag in tag_str:
        if re.match('^[a-zA-Z]*$', tag) is None:
            raise ValidationError("Only one word per tag is allowed :|")
