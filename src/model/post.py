import database
from config import Configuration

import random
import time

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
    
    @staticmethod
    def create_new(content_type, content_string, source=None, description=None, reference=None, signature=None, tags=[]):
        """
        Creates a brand new post Object and returns it
        """
        return post(
            post_id=random.randint(1,2**32),
            timestamp=int(time.time()),
            origin=Configuration().base_url,
            content_type=content_type,
            content_string=content_string,
            source=source,
            description=description,
            reference=reference,
            tags=tags
        )

class image_post(post):
    def __init__(self, post_id, timestamp, origin, image_url, thumb_url,  source=None, description=None, reference=None, signature=None, tags=[]):
        post.__init__(self,
            post_id=post_id,
            timestamp=timestamp,
            origin=origin,
            content_type="image",
            content_string=image_url+";"+thumb_url,
            source=source,
            description=description,
            reference=reference,
            signature=signature,
            tags=tags
        )
        self.image_url = image_url
        self.thumb_url = thumb_url

    @staticmethod
    def create_new(image_url, thumb_url ,source=None, description=None, reference=None, signature=None, tags=[]):
        return image_post(
            post_id=random.randint(1,2**32),
            timestamp=int(time.time()),
            origin=Configuration().base_url,
            image_url=image_url,
            thumb_url=thumb_url,
            source=source,
            description=description,
            reference=reference,
            signature=signature,
            tags=tags
        )

def sql_post_factory(cursor, row):
    d = {}
    for index, column in enumerate(cursor.description):
        d[column[0]] = row[index]

    if d['content_type'] == "image":
        p = image_post(
            post_id=d['post_id'],
            timestamp=d['timestamp'],
            origin=d['origin'],
            image_url=d['content_string'].split(';')[0],
            thumb_url=d['content_string'].split(';')[1],
            source=d['source'],
            description=d['description'],
            reference=d['reference'],
            signature=d['signature'],
            tags=None  #TODO change when tags are supported
        )
    else:
        p = post(None, None, None, None, None)
        p.__dict__ = d #TODO hacketyhack
    
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

    # post
    cursor = db.connection.cursor()
    cursor.execute("INSERT INTO sftib_posts (post_id, timestamp, origin, content_type, content_string, source, description, reference, signature) VALUES (?,?,?,?,?,?,?,?,?)", (post.post_id, post.timestamp, post.origin, post.content_type, post.content_string, post.source, post.description, post.reference, post.signature))
    post_id = cursor.lastrowid
    
    # tag post 
    cursor = db.connection.cursor()
    
    for tag in post.tags:
        cursor.execute("INSERT INTO sftib_tags ( tag ) VALUES ( ? );", (tag,))
        cursor.execute("INSERT INTO sftib_post_is_tagged ( post_id, tag_id ) VALUES (?, (SELECT id FROM sftib_tags WHERE tag=? LIMIT 1));", (post_id, tag))
    db.connection.commit()

