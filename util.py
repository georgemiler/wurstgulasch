import os
from hashlib import md5

from PIL import Image

from config import Configuration

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
    offset = max(width, height)/2
    if width < height:
        box = (0, offset, size, size+offset)
    else:
        box = (offset, 0, size+offset, size)
    image = image.crop(box)
    return image
