import os
import random
import time
from hashlib import md5
import json
from PIL import Image
from StringIO import StringIO

from werkzeug.wrappers import Response
from werkzeug.utils import redirect

from jinja2 import Environment, FileSystemLoader

import sqlalchemy
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import util
from util import render_template
import model
from model import tag, post, image_post, friend, user
from config import Configuration

from wtforms import Form, BooleanField, TextField, PasswordField, TextAreaField, validators
from wtfrecaptcha.fields import RecaptchaField

def authorized(function):
    """
    checks if the username in the is identic to <username>, raises Exception('InsufficientPrivileges') otherwise.
    """
    def inner(*args, **kwargs):
        environment = args[1]
        try:
            username = kwargs['username']
        except KeyError, e:
            raise Exception('NoUsernamePassed')
        
        if environment['beaker.session']['username'] == username:
             return function(*args, **kwargs)
        else:
             raise Exception("InsufficientPrivileges")

    return inner

def admin(function):
    """
    checks if the username in the session is 'admin', raises Exception('InsufficientPrivileges') otherwise.
    """
    def inner(*args, **kwargs):
        environment = args[1]
        try:
            if environment['beaker.session']['username'] == "admin":
                return function(*args, **kwargs)
            else:
                raise Exception("InsufficientPrivileges")
        except KeyError, e:
            raise Exception("InsufficientPrivileges")

    return inner

def get_user_obj(username, session):
    """
    returns the user object with the name <username>.

    Raises Exception('NoSuchUser') if <username> is not known to the system.
    """
    try:
        u =session.query(user).filter(user.name == username).one()
    except Exception, e:
        raise Exception('NoSuchUser')

    if not u:
        raise Exception('NoSuchUser')
    return u

def web_logout(request, environment, session):
    """
    Deletes the client's session
    """
    session = environment['beaker.session']
    session.delete()
    return redirect('/') 

def web_login(request, environment, session):
    """
    verifies username and password, sets the username attribute of the session accordingly.

    Possible errortype values:
     * 'LoginInvalid' if the the login was not successful.
    """
    class LoginForm(Form):
        username = TextField('username', [validators.Required()])
        password = PasswordField('password', [validators.Required()])

    if request.method == "POST":
        form = LoginForm(request.form)
        if form.validate():
            try:
                user_obj = get_user_obj(form.username.data, session)
            except Exception, e:
                return render_template("web_login.htmljinja", environment, form=form, error="Error: Username and password do not match!")
            #TODO hash
            if user_obj.passwordhash == form.password.data:
                http_session = environment['beaker.session']
                http_session['username'] = user_obj.name
                http_session.save()
                return redirect('/')
        else:
            return render_template("web_login.htmljinja", environment, form=form)
    else:
        form = LoginForm()
        return render_template("web_login.htmljinja", environment, form=form)

def json_since(request, environment, session, username, timestamp):
    """
    returns json representations of <username>'s posts since <timestamp>, in consequence an empty array
    if there are none.
    if an error occurs, a json representation of the error handling is returned.

    Possible errortype values:
     * 'NoSuchUser'
    """
    try:
        u = get_user_obj(username, s)
    except Exception, e:
        return Response(json.dumps({'success': False, 'errortype': 'NoSuchUser'}), content_type="text/json")

    posts = session.query(post).filter(post.owner == u).filter(post.timestamp >= int(timestamp)).all() 
    dicts = [ x.to_serializable_dict() for x in posts ]
    return Response(json.dumps(dicts, encoding="utf-8"), content_type="text/json")

def json_last(request, environment, session, username, count):
    """
    returns json representations of <username>'s last <count> posts, 
    in consequence an empty array if there are none.
    if an error occurs, a json representation of the error handling is returned.

    Possible errortype values:
     * 'NoSuchUser'
    """
    try:
        u = get_user_obj(username, s)
    except Exception, e:
        return Response(json.dumps({'success': False, 'errortype': 'NoSuchUser'}), content_type="text/json")

    posts = session.query(post).filter(post.owner == u).order_by(desc(post.timestamp)).limit(int(count)).all() 
    dicts = [ x.to_serializable_dict() for x in posts ]
    return Response(json.dumps(dicts, encoding="utf-8"), content_type="text/json")


def json_user_info(request, environment, session, username):
    """
    retunrns a json representation of some of <username>'s user data.
    if an error occurs, a json representation of the standard error handling is returned.

    Possible errortype values:
     * 'NoSuchUser' if the <username> is unknown to the system.

    """
    try:
        user = get_user_obj(username, session)
    except Exception, e:
        return  Response(json.dumps({'success': False, 'errortype': 'NoSuchUser'}), content_type="text/json")
    
    userdict = user.to_serializable_dict()
    return Response(json.dumps(userdict, encoding="utf-8"), content_type="text/json")


def web_view_user_posts(request, environment, session, username, page=1, posts_per_page=30):
    """
    returns the <page> <posts_per_page> posts created by <username> as 'posts', <username>'s 
    user object as 'user', an empty array if there aren't any.

    Possible errortype values are:
    * 'NoSuchUser' if <username> is unknown to the system.

    May raise the following Exceptions:
    * Exception('NoSuchUser')
    """

    u = get_user_obj(username, session)

    origin = Configuration().base_url+u.name
    query = session.query(post).filter(post.owner == u).filter(post.origin == origin).offset((int(page)-1)*posts_per_page).limit(posts_per_page)
    posts = [p.downcast() for p in query.all()]
    return render_template("web_view_user_posts.htmljinja", environment, posts=posts, user=u) 

@authorized
def web_view_stream(request, environment, session, username, page=1, posts_per_page=30):
    """
    returns the <page> <posts_per_page> posts created by <username> as 'posts', <username>'s 
    user object as 'user', an empty array if there aren't any.

    Possible errortype values are:
     * 'InputMakesNoSense' if at least one of <page> or <posts_per_page> is negative

    May raise the following Exceptions:
     * Exception('NoSuchUser')
     * Exception('InsufficientPrivileges')
    """
    
    if page < 0 or posts_per_page < 0:
        raise Exception('InputMakesNoSense') 

    # may raise Exception('NoSuchUser')
    u = get_user_obj(username, session)
    
    posts = session.query(post).filter(post.owner == u).offset((int(page)-1)*posts_per_page).limit(posts_per_page)

    return render_template("web_view_stream.htmljinja", environment, posts=posts, user=u) 

@authorized
def web_view_stream_tag(request, environment, session, username, tagstr, page=1, posts_per_page=1):
    """
    returns the <page> <posts_per_page> posts owned by <username> and tagged with <tagstr> as 'posts' and the <username>'s 
    user object as 'user'

    Possible errortype values are:
     * 

    May raise the following Exceptions:
     * Exception('NoSuchUser')
     * Exception('InsufficientPrivileges')
     * Exception('InputMakesNoSense')
     * Exception('TagNotFound')
    """
    
    u = get_user_obj(username, session)

    #identify tag
    res = session.query(tag).filter(tag.tag == tagstr).all()
    if res:
        tag_found = res[0]
        posts = tag_found.posts
    else:
        raise Exception("TagNotFound")
    return render_template("web_view_stream_tag.htmljinja", environment, posts=posts, tag=tag_found, show_tags=True, user=u)

@authorized
def web_insert_post(request, environment, session, username):
    """
    Saves a post to <username>'s wurstgulasch.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """ 
    u = get_user_obj(username, session)
    if request.method == "POST":
        # find out content type
        try:
            content_type = request.form['content_type']
        except Exception,e:
            raise Exception("No Content Type was passed!")

        # different content types = different methods
        if content_type == "image":
            # figure out if source is URL or uploaded file and acquire content + mimetype
            file_obj = request.files.get('file')
            if file_obj:
                mimetype = file_obj.content_type
            elif request.form['content_string'] != None:
                # TODO verify URL
                from urllib import urlopen
                file_obj = urlopen(request.form['content_string'])
                mimetype = file_ob.info().gettype()
            else:
                raise Exception("No Data given")
            
            filetype = util.check_mimetype(mimetype, ["image"], ["jpeg", "png", "gif", "tiff"])
            # TODO check for exceptions
            buf_image = file_obj.read();
            image = Image.open(StringIO(buf_image))
            thumbnail = util.generate_thumbnail(image, 300)

            assetspath = os.path.join(Configuration().base_path, 'assets')
            filename = md5(buf_image).hexdigest() + "." + filetype;
            imagepath = os.path.join(assetspath, filename)
            thumbnailpath = os.path.join(assetspath, "thumb_" + filename)

            # TODO check for exceptions
            image.save(imagepath)
            thumbnail.save(thumbnailpath)
            
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
 
            return render_template("web_insert_post.htmljinja", environment)
  
        elif content_type == "video":
            pass
        
        else:
            raise Exception("Unknown Content type!")
             
    else:
        return render_template("web_insert_post.htmljinja", environment)

def web_view_post_detail(request, environment, session, username, postid):
    """
    Saves a post to <username>'s wurstgulasch.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """
    u = get_user_obj(username, session)
    
    p = session.query(model.post).filter(post.post_id == int(postid)).all()[0]
    return render_template("web_view_post_detail.htmljinja", environment, post=p, user=u, show_tags=True)

@authorized
def web_view_friends(request, environment, session, username):
    """
    Saves a post to <username>'s wurstgulasch.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """ 
    u = get_user_obj(username, session)

    friends = session.query(model.friend).filter(model.friend.owner == u).all()
    return render_template("web_view_friends.htmljinja", environment, friends=friends)

@authorized
def web_add_friends(request, environment, session, username):
    """
    Saves a post to <username>'s wurstgulasch.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """
    class AddFriendForm(Form):
        handle = TextField("FriendHandle", [validators.Required()]) 
         
    u = get_user_obj(username, session)
    
    if request.method == "POST":
        form = AddFriendForm(request.form) 
        if form.validate():
            screenname, url = form.handle.data.split('@')
            tmp = friend(screenname=screenname, url=url, lastupdated=0)
            
            # add owner
            # TODO replace by proper code once user and session handling is in place
            tmp.owner = u
            
            session.add(tmp)
            session.commit()
            return redirect('/'+u.name+'/friends')
    else:
        form = AddFriendForm()
        return render_template("web_add_friends.htmljinja", environment, form=form) 

@authorized
def web_delete_friend(request, environment, session, username, friendid):
    user_obj = get_user_obj(username, session)
    friend_obj = session.query(friend).filter(friend.id == friendid).one()
    if friend_obj in user_obj.friends:
        session.delete(friend_obj)
        session.commit()
    return redirect('/'+username+'/friends') 

def web_view_profile(request, environment, session, username):
    """
    Saves a post to <username>'s wurstgulasch.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """
    u = get_user_obj(username, session)
    return render_template("web_view_profile.htmljinja", environment, user=u)

@authorized
def web_change_profile(request, environment, session, username):
    """
    makes changes to <username>'s user object

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """
    u = get_user_obj(username, session)

    if request.method == 'POST':
        # TODO: strip HTML
        u.tagline = request.form['tagline']
        u.bio = request.form['bio']

        # avatar
        uploaded = request.files.get('avatar')
        if uploaded:
            mimetype = uploaded.content_type
            try:
                filetype = util.check_mimetype(mimetype, ["image"], ["jpeg", "png", "gif", "tiff"])
            except Exception, e:
                pass # TODO no valid filetype
            else:
                buf_image = uploaded.read()
                image = util.force_quadratic(Image.open(StringIO(buf_image)))
                thumbnail = util.generate_thumbnail(image, 50)

                assetspath = os.path.join(Configuration().base_path, 'assets')
                filename = "avatar_" + md5(buf_image).hexdigest() + "." + filetype;
                imagepath = os.path.join(assetspath, filename)
                thumbnailpath = os.path.join(assetspath, "thumb_" + filename)

                image.save(imagepath)
                thumbnail.save(thumbnailpath)

                u.avatar_url = Configuration().base_url+'assets/'+filename
                u.avatar_small_url = Configuration().base_url+'assets/thumb_'+filename

        # TODO: use hash
        if request.form['password'] == request.form['password2'] and request.form['password'] != '':
            u.passwordhash = request.form['password']
        
        session.commit()
        return render_template("web_change_profile.htmljinja", environment, success=True, user=u)
    
    else:
        return render_template("web_change_profile.htmljinja", environment, user=u)
@admin
def admin_view_users(request, environment, session):
    """
    returns all user objects known to the system.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """

    users = session.query(model.user).all()

    return render_template("admin_view_users.htmljinja", environment, users=users)

@admin
def admin_create_user(request, environment, session):
    """
    creates a new user and adds it to the database.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """
    class CreateUserForm(Form):
        username = TextField('Username', [validators.Required()])
        password = TextField('Password', [validators.Required()])    

    if request.method == 'POST':
        form = CreateUserForm(request.form)
        if form.validate():
            username = form.username.data.strip()
            password = form.password.data
            u = model.user(name = username, passwordhash = password) #TODO: hash password
            session.add(u)
            try:
                session.commit()
            except IntegrityError, e:
                return render_template("admin_create_user.htmljinja", environment, success=False, form=form)
            
            return redirect('/admin/users/view')
        else:
            return render_template("admin_create_user.htmljinja", environment, success=False, form=form)
    else:
        form = CreateUserForm()
        return render_template("admin_create_user.htmljinja", environment, form=form)

@admin
def admin_reset_password(request, environment, session, username):
    """
    resets  <username>'s password

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """
    class ResetPasswordForm(Form):
        password = TextField("password", [validators.Required()])
    
    u = get_user_obj(username, session)

    if request.method == 'POST':
        form = ResetPasswordForm(request.form)
        if form.validate():
            u.passwordhash = form.password.data
            session.commit()
            return redirect('/admin/users/view')
    else:
        form = ResetPasswordForm()
        return render_template("admin_reset_password.htmljinja", environment, success=False, user=u, form=form)

@admin  
def admin_delete_user(request, environment, session, username):
    """
    deletes <username>'s user object from the database

    Possible errortypes are:
     * 
    1May raise the following Exceptions:
     * 
    """
    # don't delete admin user
    if username == 'admin':
        return render_template("admin_delete_user.htmljinja", environment, success=False)

    try:
        user = get_user_obj(username, session)
    except NoResultFound, e:
        return render_template("admin_delete_user.htmljinja", environment, success=False)
    # delete all posts by user
    posts = session.query(model.post).filter(model.post.owner == user).all()
    for post in posts:
        session.delete(post)
    # delete friends
    for friend in user.friends:
        session.delete(friend)
    session.delete(user)
    session.commit()

    return redirect('/admin/users/view')

def default(request, environment, session):
    """
    returns an empty dictionary.

    Possible errortypes are:
     * 
    May raise the following Exceptions:
     * 
    """
    return render_template("default.htmljinja", environment)
