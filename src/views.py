#!/usr/bin/python2

import pyratemp
import database

import cgitb
cgitb.enable()

db = database.database_connection(filename="lol.db")

def print_header(content_type="text/html"):
    print("Content-Type: %s" % (content_type,))
    print("Content-Encoding: utf-8")
    print("")

def view_user_posts_json():
    print_header(content_type="text/json")
    posts = db.get_posts()
    temp = pyratemp.Template(filename="templates/json.tpl")
    print(temp(post=posts[0]))

def view_user_posts():
    pass

view_user_posts_json()
