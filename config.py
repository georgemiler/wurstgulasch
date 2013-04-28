import ConfigParser


class Configuration:
    # Borg Pattern
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def load_from_file(self, filename="wurstgulasch.cfg"):
        parser = ConfigParser.RawConfigParser()
        parser.read(filename)

        self.instance_name = parser.get("base", "instance_name")
        self.instance_owner = parser.get("base", "instance_owner")
        self.base_url = parser.get("base", "base_url")
        self.base_path = parser.get("base", "base_path")
        self.base_domain = parser.get("base", "base_domain")

        self.database_uri = parser.get("db", "database_uri")
