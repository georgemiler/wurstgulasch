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
