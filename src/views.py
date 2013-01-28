import os
import random
import time
from hashlib import md5

from werkzeug.wrappers import Response

from jinja2 import Environment, FileSystemLoader

from model import post
from config import Configuration

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

def generate_thumbnail(folder, filename):
    from PIL import Image
    im = Image.open(os.path.join(folder, filename))
                    
    # guttenberg'd from:
    #   http://jargonsummary.wordpress.com/2011/01/08/how-to-resize-images-with-python/
    # TODO: Improve algorithm
    basewidth = 300
    wpercent = (basewidth / float(im.size[0]))
    hsize = int((float(im.size[1]) * float(wpercent)))
    im = im.resize((basewidth, hsize), Image.ANTIALIAS)
    thumbpath = os.path.join(folder, "thumb_"+filename)
    im.save(thumbpath)
    return thumbpath

def json_since(request, timestamp):
    posts = post.get_posts(since=timestamp)
    out = render_template(template_name="json.jinja", posts=posts)
    return Response(out, mimetype="text/plain")

def json_last(request, count):
    posts = post.get_posts(count=count)
    out = render_template(template_name="json.tpl", posts=posts)
    return Response(out, mimetype="text/plain")

def web_view_posts(request, page=1, posts_per_page=30):
    posts = post.get_posts_pagewise(page=int(page), posts_per_page=posts_per_page)
    out = render_template(template_name="web_view_posts.htmljinja", posts=posts)
    return Response(out, mimetype="text/html")        

def web_insert_post(request):
    if request.method == "POST":
        # find out content type
        try:
            content_type = request.form['content_type']
        except Exception,e:
            raise Exception("No Content Type was passed!")

        # different content types = different methods
        if content_type == "image":
            # figure out if source is URL or uploaded file and acquire content + mimetype
            uploaded = request.files.get('file')
            if uploaded:
                image = uploaded.read()
                mimetype = uploaded.content_type
            elif request.form['content_string'] != None:
                # TODO verify URL
                from urllib import urlopen
                f = urlopen(request.form['content_string'])
                image = f.read()
                mimetype = f.info().gettype()
            else:
                raise Exception("No Data given")
            
            # continue file processing
            main_type = mimetype.split('/')[0]
            sub_type = mimetype.split('/')[1]
            
            if main_type != "image" or sub_type not in ['jpeg', 'png', 'gif', 'tiff']:
                raise Exception("Unsupported File Type")
            
            filename = md5(image).hexdigest() + "." + sub_type
            image_path = os.path.join('assets', filename)
            
            f = open(image_path, 'w')
            f.write(image)
            f.close()
    
            thumb_path = generate_thumbnail('assets', filename) 
            image_url = Configuration().base_url+image_path           
            thumb_url = Configuration().base_url+thumb_path

            # parse tags
            tags = [ t.strip() for t in request.form['tags'].split(',') ]
            
            tmp = post.image_post.create_new(
                image_url=image_url,
                thumb_url=thumb_url,
                source=request.form['source'],
                tags=tags,
                description=request.form['description'],
                reference=None,
                signature=None
            ) 
            
            post.insert_post(tmp) 
            return Response('This was a triumph', mimetype="text/plain") 
  
        elif content_type == "video":
            pass
        
        else:
            raise Exception("Unknown Content type!")
             
    else:
        out = render_template('web_insert_post.html')
        return Response(out, mimetype="text/html")

def default(request):
    return Response('lol')
