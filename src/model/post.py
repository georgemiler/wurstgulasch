import database
from config import Configuration

class post:
    def __init__(self, post_id, timestamp, origin, content_type, content_string, source=None, description=None, reference=None, signature=None, tags=[]):
        self.post_id = post_id
        self.timestamp = timestamp
        self.origin = origin
        self.content_type = content_type
        self.content_string = content_string
        self.source = source
        self.tags = tags
        self.description = description
        self.reference = reference
        self.signature = signature

    def __str__(self):
        return "<Post:"+str(self.post_id)+">"

def sql_post_factory(cursor, row):
    
    p = post(None, None, None, None, None, None)

    for index, column in enumerate(cursor.description):
        if column[0] != 'id':  # We don't need the internal database ID!
            p.__dict__[column[0]] = row[index]
    
    return p
    

def get_posts_pagewise(page, posts_per_page=30):
    db = database.database_connection(filename=Configuration().database_filename)
    db.connection.row_factory = sql_post_factory
    cursor = db.connection.cursor()
    cursor.execute("SELECT * from sftib_posts ORDER BY timestamp LIMIT ?,?", ((page-1)*posts_per_page, posts_per_page))
    posts = cursor.fetchall()
    return posts

def get_posts(since=None, count=None):
    db = database.database_connection(filename=Configuration().database_filename)
    db.connection.row_factory = sql_post_factory

    cursor = db.connection.cursor()
    if since == None and count == None:
        cursor.execute("SELECT * FROM sftib_posts ORDER BY timestamp;")  # TODO include tags
    elif since != None and count == None:
        cursor.execute("SELECT * FROM sftib_posts WHERE timestamp > ? ORDER BY timestamp;", (since,))
    elif since == None and count != None:
        cursor.execute("SELECT * FROM sftib_posts ORDER BY timestamp LIMIT ?", (count,))
    else:
        cursor.execute("SELECT * FROM sftib_posts ORDER BY timestamp LIMIT 30")
    posts = cursor.fetchall()

    return posts

def insert_post(post):
    db = database.database_connection(filename=Configuration().database_filename)
    cursor = db.connection.cursor()
    
    cursor.execute("INSERT INTO sftib_posts (post_id, timestamp, origin, content_type, content_string, source, description, reference, signature) VALUES (?,?,?,?,?,?,?,?,?)", (post.post_id, post.timestamp, post.origin, post.content_type, post.content_string, post.source, post.description, post.reference, post.signature))
    db.connection.commit()
