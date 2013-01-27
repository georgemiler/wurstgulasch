import os
import random
import time

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
    return Response(out, mimetype="text/plain")

def json_last(request, count):
    posts = post.get_posts(count=count)
    out = render_template(template_name="json.tpl", posts=posts)
    return Response(out, mimetype="text/plain")

def web_view_posts(request, page=1, posts_per_page=30):
    posts = post.get_posts_pagewise(page=int(page), posts_per_page=posts_per_page)
    out = render_template(template_name="web_view_posts.tpl", posts=posts)
    return Response(out, mimetype="text/html")        

def web_insert_post(request):
    if request.method == "POST":
        
        # TODO: Verify contents
    
        if request.form['content_string'] == None or request.form['content_string'] == "":
            # either we have a file upload or the request is incomplete!
            uploaded = request.files.get('file')
            if uploaded:
                mimetype = uploaded.content_type
                if mimetype.split('/')[0] == "image" and mimetype.split('/')[1] in ['jpeg', 'png', 'gif', 'tiff']:
                    from hashlib import md5
                    hash = md5(uploaded.read())
                    uploaded.seek(0)
                    filename = str(hash.hexdigest()) + "." + mimetype.split('/')[1]
                    uploaded.save(os.path.join('assets', filename))
                    uploaded.seek(0)
                    from PIL import Image
                    im = Image.open(os.path.join('assets', filename))
                    
                    # guttenberg'd from:
                    #   http://jargonsummary.wordpress.com/2011/01/08/how-to-resize-images-with-python/
                    # TODO: Improve algorithm
                    basewidth = 300
                    wpercent = (basewidth / float(im.size[0]))
                    hsize = int((float(im.size[1]) * float(wpercent)))
                    im = im.resize((basewidth, hsize), Image.ANTIALIAS)
                    im.save(os.path.join('assets', 'thumb_'+filename))
                    
                    # TODO implement size check
                else:
                    raise Exception("Invalid File uploaded!")
            else:
                raise Exception("Incomplete request!")

        tmp = post.post(
            post_id=random.randint(1,2**32),
            timestamp=int(time.time()),
            origin="http://dev.img.sft.mx/",
            content_type=request.form['content_type'],
            content_string=request.form['content_string'],
            source=request.form['source'],
            tags=None,
            description=request.form['description'],
            reference=None,
            signature=None
        )
 
        post.insert_post(tmp) 
        return Response('This was a triumph', mimetype="text/plain") 
    else:
        out = render_template('web_insert_post.html')
        return Response(out, mimetype="text/html")

def default(request):
    return Response('lol')
