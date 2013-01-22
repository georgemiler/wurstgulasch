import sqlite3 as database_of_choice
from post import post

class database_connection():
    def __init__(self, name=None, host=None, port=None, username=None, password=None, filename=None):
        try:
            self.connection = database_of_choice.connect(filename)
        except Exception as e:
            raise Exception("Fehler bei der Datenbankverbindung: "+str(e))

    def get_posts(self, since=None, user=None):
        cursor = self.connection.cursor()
        
        basequery = "select post_id, timestamp, origin, content_type, content_string, source, description, reference, signature from sftib_posts"

        if since != None and user != None:
            query = basequery + " where timestamp>? and origin=?;"
            params = (since, user)
        elif since == None and user != None:
            query = basequery + " where user=?;"
            params = (user,)
        elif since != None and user == None:
            query = basequery + " where timestamp > ?;"
            params = (since,)
        elif since == None and user == None:
            query = basequery + ";"
            params = None
        

        try:
            if params == None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)

            results = cursor.fetchall()
        except Exception as e:
            raise Exception("Fehler beim Ausfuehren des SQL querys: "+str(e))

        posts = []

        for line in results:
            #post_id, timestamp, origin, content_type, content_string, source, description, reference, signature = line
            #posts.append(post(post_id=post_id, timestamp=timestamp, content_type=content_type, content_string=content_string, source=source, description=description, reference=reference, signature=signature))
            tmp = post(*line)
            posts.append(tmp)

        return posts 
