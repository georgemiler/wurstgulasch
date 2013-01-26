#!/usr/bin/python2
from werkzeug.wrappers import Response
import pyratemp
from model import post

def json_since(request, timestamp):
    posts = post.get_posts()
    tpl = pyratemp.Template(filename="templates/json.tpl")
    return Response(tpl(posts=posts))

def json_last(request, count):
    posts = post.get_posts(count=count)
    tpl = pyratemp.Template(filename="templates/json.tpl")
    return Response(tpl(posts=posts))

def default(request):
    return Response('lol')
