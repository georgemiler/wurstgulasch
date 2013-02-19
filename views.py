import os
import random
import time
from hashlib import md5
import json

from werkzeug.wrappers import Response
from werkzeug.utils import redirect

from jinja2 import Environment, FileSystemLoader

import sqlalchemy
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import model
from model import tag, post, image_post, friend, user
from config import Configuration

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

def verify_user(environment, username):
    try:
        if environment['beaker.session']['username'] == username:
            return True
        else:
            raise Exception("I can't let you do that, Dave")
    except KeyError, e:
        raise Exception("I can't let you do that, Dave")

def verify_admin(environment):
	try:
		if environment['beaker.session']['username'] == "admin":
			return True
		else:
			raise Exception("I can't let you do that, Dave")
	except KeyError, e:
		raise Exception("I can't let you do that, Dave")

def get_user_obj(username, session):
    return session.query(user).filter(user.name == username).one()

def web_logout(request, environment):
    session = environment['beaker.session']
    session.delete()
    return {}

def web_login(request, environment):
    if request.method == "POST":
        session = model.Session()
        try:
            user_obj = session.query(user).filter(user.name == request.form['username']).one()
            if user_obj and user_obj.passwordhash == request.form['password']:
                web_sess = environment['beaker.session']
                web_sess['username'] = user_obj.name
                web_sess.save()
                return {'success': True}
            else:
                return {'success': False}
        except sqlalchemy.orm.exc.NoResultFound:
            return {'success': False}
    else:
        return {'success': False}

def json_since(request, environment, username, timestamp):
    s = model.Session()
    u = get_user_obj(username, s)

    posts = s.query(post).filter(post.owner == u).filter(post.timestamp >= int(timestamp)).all() 
    dicts = [ x.to_serializable_dict() for x in posts ]
    return {'string': json.dumps(dicts, encoding="utf-8")}

def json_last(request, environment, username, count):
    s = model.Session()
    u = get_user_obj(username, s)

    posts = s.query(post).filter(post.owner == u).order_by(desc(post.timestamp)).limit(int(count)).all() 
    dicts = [ x.to_serializable_dict() for x in posts ]
    return {'string': json.dumps(dicts, encoding="utf-8")}

def web_view_user_posts(request, environment, username, page=1, posts_per_page=30):
    session = model.Session()
    u = get_user_obj(username, session)

    origin = Configuration().base_url+u.name
    query = model.Session().query(post).filter(post.owner == u).filter(post.origin == origin).offset((int(page)-1)*posts_per_page).limit(posts_per_page)
    posts = [p.downcast() for p in query.all()]
    return {'posts': posts, 'user': u} 

def web_view_stream(request, environment, username):
    session = model.Session()
    u = get_user_obj(username, session)
    verify_user(environment, username)

    posts = session.query(post).filter(post.owner == u)

    return {'posts': posts, 'user': u, 'show_tags': True}


def web_view_stream_tag(request, environment, username, tagstr, page=40):
    session = model.Session()
    u = get_user_obj(username, session)
    verify_user(environment, username) 

    #identify tag
    res = session.query(tag).filter(tag.tag == tagstr).all()
    if res:
        tag_found = res[0]
        posts = tag_found.posts
    else:
        raise Exception("Tag not found!")

    return {'posts': posts, 'tag': tag_found, 'show_tags': True, 'user': u}

def web_insert_post(request, environment, username):
    session = model.Session()
    u = get_user_obj(username, session)
    verify_user(environment, username)
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
            assets_path = os.path.join(Configuration().base_path, 'assets')
            image_path = os.path.join(assets_path, filename)
            
            f = open(image_path, 'w')
            f.write(image)
            f.close()
    
            thumb_path = generate_thumbnail(assets_path, filename) 
            image_url = Configuration().base_url+'assets/'+filename          
            thumb_url = Configuration().base_url+'assets/thumb_'+filename

                   
            tmp = image_post(
                image_url=image_url,
                thumb_url=thumb_url,
                source=request.form['source'],
                tags=[],
                description=request.form['description'],
                reference=None,
                signature=None
            ) 
            
            # add owner and origin
            tmp.owner = u
            tmp.origin = Configuration().base_url+u.name

            # add tags
            tag_strings = [ t.strip() for t in request.form['tags'].split(',') ]
            for tag_str in tag_strings:
                if tag_str != '':
                    res = session.query(tag).filter(tag.tag == tag_str).all()
                    if res:
                        tmp.tags.append(res[0])
                    else:
                        new_tag = tag(tag_str)
                        session.add(new_tag)
                        tmp.tags.append(new_tag)
            
            session.add(tmp)
            session.commit()
 
            return {}           
  
        elif content_type == "video":
            pass
        
        else:
            raise Exception("Unknown Content type!")
             
    else:
        return {} 

def web_view_friends(request, environment, username):
    session = model.Session()
    u = get_user_obj(username, session)
    verify_user(environment, username)

    friends = session.query(model.friend).filter(model.friend.owner == u).all()

    return {'friends': friends}

def web_add_friends(request, environment, username):
    session = model.Session()

    u = get_user_obj(username, session)
    verify_user(environment, username) 
    
    if request.method == "POST":
        if request.form['url'] != "" and request.form['screenname'] != "":
            tmp = friend(screenname=request.form['screenname'], url=request.form['url'], lastupdated=0)
            
            # add owner
            # TODO replace by proper code once user and session handling is in place
            tmp.owner = u
            
            session.add(tmp)
            session.commit()
            return {}
    else:
        return {}

def web_view_profile(request, environment, username):
    s = model.Session()
    u = get_user_obj(username, s)

    return {'user': u}

def web_change_profile(request, environment, username):
    s = model.Session()
    u = get_user_obj(username, s)
    verify_user(environment, username)

    if request.method == 'POST':
        # TODO: strip HTML
        u.tagline = request.form['tagline']
        u.bio = request.form['bio']
        
        # TODO: use hash
        if request.form['password'] == request.form['password2'] and request.form['password'] != '':
            u.passwordhash = request.form['password']
        
        s.commit()
        return {'success': True, 'user': u}
    
    else:
        return {'user': u}

def admin_view_users(request, environment):
	verify_admin(environment)
	s = model.Session()

	users = s.query(model.user).all()

	return {'users' : users}

def admin_create_user(request, environment):
	verify_admin(environment)
	s = model.Session()
	
	if request.method == 'POST':
		username = request.form['username'].strip(" \t") #remove leading/trailing whitespaces
		password = request.form['password']
		if username != "" and password != "":
			u = model.user(name = username, passwordhash = password) #TODO: hash password
			s.add(u)
			try:
				s.commit()
			except IntegrityError, e:
				return {'success': False}
			return {'success': True}	
		else:
			return {'success' : False}
	else:
		return {}

def admin_reset_password(request, environment, username):
	verify_admin(environment)
	s = model.Session()
	try:
		u = s.query(model.user).filter(model.user.name == username).one()
	except NoResultFound, e:
		raise Exception("User " + username + " does not exist")

	if request.method == 'POST':
		password = request.form['password']
		if password == "":
			return {'success' : False, 'user' : u}
		u.passwordhash = password
		s.commit()
		return {'success' : True, 'user' : u}
	else:
		return {'success' : False, 'user' : u}

		
def admin_delete_user(request, environment, username):
	verify_admin(environment)
	s = model.Session()
	# don't delete admin user
	if username == 'admin':
		return {'success': False}

	try:
		user = s.query(model.user).filter(model.user.name == username).one()
	except NoResultFound, e:
		return {'success' : False}
	# delete all posts by user
	posts = s.query(model.post).filter(model.post.owner == user).all()
	for post in posts:
		s.delete(post)
	# delete friends
	for friend in user.friends:
		s.delete(friend)
	s.delete(user)
	s.commit()

	return{'success' : True}


def default(request, environment):
    return {}
