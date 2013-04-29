import os

from hashlib import md5
import json
from PIL import Image
from StringIO import StringIO

from werkzeug.wrappers import Response
from werkzeug.utils import redirect

from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import util
from util import render_template
import model
from model import tag, post, user, identity
from config import Configuration

from wtforms import Form, TextField, FileField, PasswordField, TextAreaField,\
    validators


def authorized(function):
    """
    checks if the username in the is identic to <username>, raises
    Exception('InsufficientPrivileges') otherwise.
    """
    def inner(*args, **kwargs):
        environment = args[1]
        try:
            username = kwargs['username']
        except KeyError:
            raise Exception('NoUsernamePassed')

        if environment['beaker.session']['username'] == username:
            return function(*args, **kwargs)
        else:
            raise Exception("InsufficientPrivileges")

    return inner


def admin(function):
    """
    checks if the username in the session is 'admin', raises
    Exception('InsufficientPrivileges') otherwise.
    """
    def inner(*args, **kwargs):
        environment = args[1]
        try:
            if environment['beaker.session']['username'] == "admin":
                return function(*args, **kwargs)
            else:
                raise Exception("InsufficientPrivileges")
        except KeyError:
            raise Exception("InsufficientPrivileges")

    return inner


def get_user_obj(username, session):
    """
    returns the user object with the name <username>.

    Raises Exception('NoSuchUser') if <username> is not known to the system.
    """
    try:
        u = session.query(user).join(identity).\
            filter(identity.username == username).one()

    except Exception:
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
    verifies username and password, sets the username attribute of the session
    accordingly.

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
            except Exception:
                return render_template("web_login.htmljinja", environment,
                                       form=form, error="Error: Username \
                                       and password do not match!")
            #TODO hash
            if user_obj.passwordhash == form.password.data:
                http_session = environment['beaker.session']
                http_session['username'] = user_obj.identity.username
                http_session.save()
                return redirect('/')
        else:
            return render_template("web_login.htmljinja", environment,
                                   form=form)
    else:
        form = LoginForm()
        return render_template("web_login.htmljinja", environment, form=form)


def json_since(request, environment, session, username, timestamp):
    """
    returns json representations of <username>'s posts since <timestamp>, in
    consequence an empty array if there are none. if an error occurs, a json
    representation of the error handling is returned.

    Possible errortype values:
     * 'NoSuchUser'
    """
    try:
        u = get_user_obj(username, session)
    except Exception:
        return Response(json.dumps(
                        {'success':     False,
                         'errortype':   'NoSuchUser'}
                        ), content_type="text/json")

    posts = session.query(post).filter(post.owner == u).\
        filter(post.timestamp >= int(timestamp)).all()
    dicts = [x.to_serializable_dict() for x in posts]
    return Response(json.dumps(dicts, encoding="utf-8"),
                    content_type="text/json")


def json_last(request, environment, session, username, count):
    """
    returns json representations of <username>'s last <count> posts,
    in consequence an empty array if there are none.
    if an error occurs, a json representation of the error handling is
    returned.

    Possible errortype values:
     * 'NoSuchUser'
    """
    try:
        u = get_user_obj(username, session)
    except Exception:
        return Response(json.dumps(
                        {'success': False, 'errortype': 'NoSuchUser'}),
                        content_type="text/json")

    posts = session.query(post).filter(post.owner == u).\
        order_by(desc(post.timestamp)).limit(int(count)).all()
    dicts = [x.to_serializable_dict() for x in posts]
    return Response(json.dumps(dicts, encoding="utf-8"),
                    content_type="text/json")


def json_user_info(request, environment, session, username):
    """
    retunrns a json representation of some of <username>'s user data.
    if an error occurs, a json representation of the standard error handling
    is returned.

    Possible errortype values:
     * 'NoSuchUser' if the <username> is unknown to the system.

    """
    try:
        user = get_user_obj(username, session)
    except Exception:
        return Response(json.dumps(
                        {'success': False, 'errortype': 'NoSuchUser'}),
                        content_type="text/json")

    userdict = user.to_serializable_dict()
    return Response(json.dumps(userdict, encoding="utf-8"),
                    content_type="text/json")


def web_view_user_posts(request, environment, session, username, page=1,
                        posts_per_page=15):
    """
    returns the <page> <posts_per_page> posts created by <username> as 'posts',
    <username>'s user object as 'user', an empty array if there aren't any.

    Possible errortype values are:
    * 'NoSuchUser' if <username> is unknown to the system.

    May raise the following Exceptions:
    * Exception('NoSuchUser')
    """

    u = get_user_obj(username, session)

    own = session.query(post.id).filter(post.owner == u.identity).subquery()
    reposts = session.query(post.id).filter(
        post.reposters.contains(u.identity)).subquery()
    total_num = session.query(model.post).filter(or_(post.id.in_(reposts), post.id.in_(own))).count()
    allposts = session.query(model.post).filter(
        or_(post.id.in_(reposts), post.id.in_(own))).offset((page-1)*posts_per_page).limit(posts_per_page).all()

    posts = [p.downcast() for p in allposts]

    return render_template("web_view_user_posts.htmljinja", environment,
                           posts=posts, page_num=page, total_num=total_num,
                           posts_per_page=posts_per_page, user=u)


@authorized
def web_view_stream(request, environment, session, username, page=1,
                    posts_per_page=15):
    """
    returns the <page> <posts_per_page> posts created by <username> as 'posts',
    <username>'s user object as 'user', an empty array if there aren't any.

    Possible errortype values are:
     * 'InputMakesNoSense' if at least one of <page> or <posts_per_page> is
       negative

    May raise the following Exceptions:
     * Exception('NoSuchUser')
     * Exception('InsufficientPrivileges')
    """

    # may raise Exception('NoSuchUser')
    u = get_user_obj(username, session)
    friend_ids = [f.id for f in u.friends]

    # one more time... with subqueries

    # friends' posts
    friendposts = session.query(model.post.id).\
        filter(model.post.owner_id.in_(friend_ids)).subquery()

    # friends' reposts
    friendreposts = session.query(model.post.id).join(model.post_reposters).\
        filter(model.post_reposters.c.identity_id.in_(friend_ids)).subquery()

    # now put it together

    posts = session.query(model.post).\
        filter(or_(model.post.id.in_(friendposts),
                   model.post.id.in_(friendreposts))).\
        offset((page-1)*posts_per_page).limit(posts_per_page).all()

    total_num = session.query(model.post).\
        filter(or_(model.post.id.in_(friendposts),
                   model.post.id.in_(friendreposts))).\
        count()

    return render_template("web_view_stream.htmljinja", environment,
                           posts=posts, user=u, page_num=page, total_num=total_num,
                           posts_per_page=posts_per_page)


@authorized
def web_view_stream_tag(request, environment, session, username, tagstr,
                        page=1, posts_per_page=15):
    """
    returns the <page> <posts_per_page> posts owned by <username> and tagged
    with <tagstr> as 'posts' and the <username>'s user object as 'user'

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
        posts = tag_found.posts[(page-1)*posts_per_page:page*posts_per_page]
        total_num = len(tag_found.posts)
    else:
        raise Exception("TagNotFound")
    return render_template("web_view_stream_tag.htmljinja", environment,
                           posts=posts, tag=tag_found, show_tags=True, user=u,
                           page_num=page, total_num=total_num,
                           posts_per_page=posts_per_page)


@authorized
def web_insert_post(request, environment, session, username, plugin_str=None):
    """
    Saves a post to <username>'s wurstgulasch.

    Possible errortypes are:
     *
    May raise the following Exceptions:
     *
    """
    if not request.method == "POST":
        if plugin_str is None:
            # list all available plugins
            pluginlist = environment['content_plugins'].keys()
            return render_template("web_choose_post_plugin.htmljinja",
                                   environment, pluginlist=pluginlist)
        else:
            # check if plugin actually exists
            if plugin_str not in environment['content_plugins'].keys():
                raise Exception('Content Plugin not found :(')
            # show the specific form
            else:
                form = environment['content_plugins'][plugin_str].\
                    CreatePostForm()
                return render_template("web_insert_post.htmljinja",
                                       environment, form=form)
    else:
        if not plugin_str is None:
            # check if plugin actually exists
            if plugin_str not in environment['content_plugins'].keys():
                raise Exception('Content Plugin not found :(')
            form = environment['content_plugins'][plugin_str].CreatePostForm(request.form)
            # create post object
            plugin_class = environment['content_plugins'][plugin_str]
            post_obj = plugin_class.from_request(form, request)

            # set user and time
            u = get_user_obj(username, session)
            post_obj.owner = u.identity
            # add tags
            tag_strings = [ t.strip() for t in request.form['tags'].split(',') ]
            for tag_str in tag_strings:
                res = session.query(tag).filter(tag.tag == tag_str).all()
                if res:
                    post_obj.tags.append(res[0])
                else:
                    new_tag = tag(tag_str)
                    session.add(new_tag)
                    post_obj.tags.append(new_tag)

            # insert into database
            session.add(post_obj)
            session.commit()

            # return to Stream
            return redirect('/' + username + '/stream')
        else:
            # this should not happen
            pass


@authorized
def json_repost(request, environment, session, username, post_id):
    u = get_user_obj(username, session)
    p = session.query(model.post).filter(model.post.post_id == post_id).one()
    p.reposters.append(u.identity)
    session.commit()
    return Response('{\'success\'=True}')


@authorized
def web_repost(request, environment, session, username, post_id):
    u = get_user_obj(environment['beaker.session']['username'], session)
    p = session.query(model.post).filter(model.post.post_id == post_id).one()
    if u.identity.username == p.owner.username:
        raise Exception('Cannot Repost your own posts.')
    p.reposters.append(u.identity)
    session.commit()
    return redirect("/" + username + "/post/" + str(post_id))


def web_view_post_detail(request, environment, session, username, postid):
    """
    Saves a post to <username>'s wurstgulasch.

    Possible errortypes are:
     *
    May raise the following Exceptions:
     *
    """
    u = get_user_obj(username, session)

    p = session.query(model.post).filter(post.post_id == int(postid),).all()[0]
    return render_template("web_view_post_detail.htmljinja", environment,
                           post=p, user=u, show_tags=True)


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

    friends = u.friends
    return render_template("web_view_friends.htmljinja", environment,
                           friends=friends)


@authorized
def web_add_friend(request, environment, session, username):
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
            # check if identity exists
            name, wurstgulasch = form.handle.data.split("@")
            if session.query(identity).\
                    filter(identity.username == name,
                           identity.wurstgulasch == wurstgulasch).\
                    count() != 0:
                new_friend = session.query(identity).\
                    filter(identity.username == name,
                           identity.wurstgulasch == wurstgulasch).one()
            else:
                new_friend = identity(name, wurstgulasch=wurstgulasch)
                session.add(new_friend)

            u.friends.append(new_friend)
            session.commit()

            return redirect('/' + username + '/friends')

    else:
        form = AddFriendForm()
        return render_template("web_add_friends.htmljinja",
                               environment, form=form)


@authorized
def web_delete_friend(request, environment, session, username, friendid):
    user_obj = get_user_obj(username, session)
    friend_obj = session.query(identity).filter(identity.id == friendid).one()
    user_obj.friends.remove(friend_obj)

    session.commit()

    return redirect('/' + username + '/friends')


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
    class changeProfileForm(Form):
        tagline = TextField("Tagline")
        bio = TextAreaField("Something about yourself")
        avatar = FileField("Your Avatar")
        password = PasswordField("New Password (leave empty if you \
                                  don't want to change it")
        password_confirm = PasswordField("Confirm new password")

    u = get_user_obj(username, session)

    if request.method == 'POST':
        form = changeProfileForm(request.form)
        # TODO: strip HTML
        u.identity.tagline = form.tagline.data
        u.identity.bio = form.bio.data

        # avatar
        uploaded = request.files.get('avatar')
        if uploaded:
            mimetype = uploaded.content_type
            try:
                filetype = util.check_mimetype(mimetype, ["image"],
                                               ["jpeg", "png", "gif", "tiff"])
            except Exception:
                # TODO no valid filetype
                pass
            else:
                buf_image = uploaded.read()
                image = util.force_quadratic(Image.open(StringIO(buf_image)))
                thumbnail = util.generate_thumbnail(image, 50)

                assetspath = os.path.join(Configuration().base_path, 'assets')
                filename = "avatar_" + md5(buf_image).hexdigest() + "." +\
                           filetype
                imagepath = os.path.join(assetspath, filename)
                thumbnailpath = os.path.join(assetspath, "thumb_" + filename)

                image.save(imagepath)
                thumbnail.save(thumbnailpath)

                u.identity.avatar_url = Configuration().base_url + 'assets/' +\
                    filename

                u.identity.avatar_small_url = Configuration().base_url +\
                    'assets/thumb_' + filename

        # TODO: use hash
        if form.password.data != "" and form.password.data == form.password_confirm.data:
            u.passwordhash = form.password.data

        session.commit()
        return render_template("web_change_profile.htmljinja", environment,
                               success=True, user=u)
    else:
        form = changeProfileForm()
        form.bio.data = u.identity.bio
        form.tagline.data = u.identity.tagline
        return render_template("web_change_profile.htmljinja", environment,
                               user=u, form=form)


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

    return render_template("admin_view_users.htmljinja", environment,
                           users=users)


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
            #TODO: hash password
            u = model.user(username, password)
            session.add(u)
            try:
                session.commit()
            except IntegrityError:
                return render_template("admin_create_user.htmljinja",
                                       environment, success=False, form=form)

            return redirect('/admin/users/view')
        else:
            return render_template("admin_create_user.htmljinja", environment,
                                   success=False, form=form)
    else:
        form = CreateUserForm()
        return render_template("admin_create_user.htmljinja", environment,
                               form=form)


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
        password = TextField("password",
                             [validators.Required()])

    u = get_user_obj(username, session)

    if request.method == 'POST':
        form = ResetPasswordForm(request.form)
        if form.validate():
            u.passwordhash = form.password.data
            session.commit()
            return redirect('/admin/users/view')
    else:
        form = ResetPasswordForm()
        return render_template("admin_reset_password.htmljinja", environment,
                               success=False, user=u, form=form)


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
        return render_template("admin_delete_user.htmljinja", environment,
                               success=False)

    try:
        user = get_user_obj(username, session)
    except NoResultFound:
        return render_template("admin_delete_user.htmljinja", environment,
                               success=False)  # delete all posts by user
    posts = session.query(model.post).filter(model.post.owner == user).all()
    for post in posts:
        session.delete(post)
    # delete friends
    #for friend in user.friends:
        #session.delete(friend)
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
