import database

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

def get_posts(since=None, count=None):
    db = database.database_connection(filename="lol.db")
    cursor = db.connection.cursor()
    if since == None and count == None:
        cursor.execute("SELECT * FROM sftib_posts ORDER BY timestamp;")  # TODO include tags
    elif since != None and count == None:
        cursor.execute("SELECT * FROM sftib_posts WHERE timestamp > ? ORDER BY timestamp;", (since,))
    elif since == None and count != None:
        cursor.execute("SELECT * FROM sftib_posts ORDER BY timestamp LIMIT ?", (count,))
    else:
        cursor.execute("SELECT * FROM sftib_posts ORDER BY timestamp LIMIT 30")
    rows = cursor.fetchall()

    posts = []
    for row in rows:
        tmp = post(
            post_id = row['post_id'],
            timestamp = row['timestamp'],
            origin = row['origin'],
            content_type = row['content_type'],
            content_string = row['content_string'],
            source = row['source'],
            tags = [], # TODO include tags
            description = row['description'],
            reference = row['reference'],
            signature = row['signature']
        )
        posts.append(tmp)

    return posts
