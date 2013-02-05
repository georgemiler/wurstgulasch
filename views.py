import os
import random
import time
from hashlib import md5
import json

from werkzeug.wrappers import Response

from jinja2 import Environment, FileSystemLoader

from sqlalchemy import desc

import model
from model import tag, post, image_post, friend, user
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
    posts = model.Session().query(post).filter(post.timestamp >= int(timestamp)).all() 
    dicts = [ x.to_serializable_dict() for x in posts ]
    return Response(json.dumps(dicts, encoding="utf-8"), mimetype="text/plain")

def json_last(request, count):
    posts = model.Session().query(post).order_by(desc(post.timestamp)).limit(int(count)).all() 
    dicts = [ x.to_serializable_dict() for x in posts ]
    return Response(json.dumps(dicts, encoding="utf-8"), mimetype="text/plain")

def web_view_posts(request, page=1, posts_per_page=30):
    query = model.Session().query(post).offset((int(page)-1)*posts_per_page).limit(posts_per_page)
    posts = [p.downcast() for p in query.all()]
    
    out = render_template(template_name="web_view_posts.htmljinja", posts=posts)
    return Response(out, mimetype="text/html")        

def web_view_posts_tag(request, tagstr):
    #identify tag
    session = model.Session()
    res = session.query(tag).filter(tag.tag == tagstr).all()
    if res:
        tag_found = res[0]
        posts = tag_found.posts
    else:
        raise Exception("Tag not found!")

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

                   
            tmp = image_post(
                image_url=image_url,
                thumb_url=thumb_url,
                source=request.form['source'],
                tags=[],
                description=request.form['description'],
                reference=None,
                signature=None
            ) 
            
            session = model.Session()

            # add owner
            # TODO replace by proper code once user and session handling is in place
            u = session.query(user).filter(user.id == 1).one()
            tmp.owner = u

            # add tags
            tag_strings = [ t.strip() for t in request.form['tags'].split(',') ]
            for tag_str in tag_strings:
                res = session.query(tag).filter(tag.tag == tag_str).all()
                if res:
                    tmp.tags.append(res[0])
                else:
                    new_tag = tag(tag_str)
                    session.add(new_tag)
                    tmp.tags.append(new_tag)
            
            session.add(tmp)
            session.commit()
            
            return Response('This was a triumph', mimetype="text/plain") 
  
        elif content_type == "video":
            pass
        
        else:
            raise Exception("Unknown Content type!")
             
    else:
        out = render_template('web_insert_post.html')
        return Response(out, mimetype="text/html")

def web_view_friends(request):
    session = model.Session()
    friends = session.query(model.friend).all()
    out = render_template('web_view_friends.htmljinja', friends=friends)
    return Response(out, mimetype="text/html")

def web_add_friends(request):
    if request.method == "POST":
        if request.form['url'] != "" and request.form['screenname'] != "":
            tmp = friend(screenname=request.form['screenname'], url=request.form['url'], lastupdated=0)
            session = model.Session()
            session.add(tmp)
            session.commit()
            return Response('Friend instance added successfully!')            
    else:
        out = render_template('web_add_friend.html')
        return Response(out, mimetype="text/html")

def default(request):
    return Response(render_template('web_general.html'), mimetype='text/html')
