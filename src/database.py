import sqlite3 as database_of_choice

# Guttenberg'd from 
#   http://docs.python.org/2.6/library/sqlite3.html
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class database_connection():
   def __init__(self, name=None, host=None, port=None, username=None, password=None, filename=None):
        try:
            self.connection = database_of_choice.connect(filename)
        except Exception as e:
            raise Exception("Fehler bei der Datenbankverbindung: "+str(e))

        self.connection.row_factory = dict_factory
