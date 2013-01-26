import ConfigParser

class Configuration:
    # Borg Pattern 
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state
    
    def loadFromFile(self,filename="wurstgulasch.cfg"):
        parser = ConfigParser.RawConfigParser()
        parser.read(filename)

        self.instance_name = parser.get("base", "instance_name")
        self.instance_owner = parser.get("base", "instance_owner")
        self.base_url = parser.get("base", "base_url")
 
        self.database_system = parser.get("db", "database_system")
        self.database_filename = parser.get("db", "database_filename")
