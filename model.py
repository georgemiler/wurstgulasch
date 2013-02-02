from config import Configuration

import random
import time

# define base for database metadata
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# hacketyhack
try:
    session = Session()
except NameError, e:
    pass

from sqlalchemy import Column, Integer, String, Table, Text, ForeignKey
from sqlalchemy.orm import relationship

class friend(Base):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True)
    screenname = Column(String)
    url = Column(String)
    lastupdated = Column(Integer)

    def __init__(self, screenname, url, lastupdated=0):
        self.screenname = screenname
        self.url = url    
        self.lastupdated = lastupdated 

post_tag = Table('post_tag', Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

class post(Base):
    __tablename__ = 'post'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer)
    timestamp = Column(Integer)
    origin = Column(String)
    content_type = Column('type', String)
    content_string = Column(String)
    source = Column(String)
    # TODO Tags as many to many relation
    tags = relationship('tag', secondary=post_tag, backref='post')
    description = Column(String)
    # TODO reference as foreign key
    # signature = Column(String)
    
    # this one says that we want inherence in a single table and that
    # the column "content_type should define which one we are
    __mapper_args__ = {'polymorphic_on': content_type}

    def __init__(self, content_type, content_string, post_id=None, timestamp=None, origin=None, source=None, description=None, reference=None, signature=None, tags=[]):
        self.post_id = post_id or random.randint(1,2**32)
        self.timestamp = timestamp or int(time.time())
        self.origin = origin or Configuration().base_url
        self.content_type = content_type
        self.content_string = content_string
        self.source = source
        # self.tags = tags
        self.description = description
        # self.reference = reference
        # self.signature = signature

    def __str__(self):
        return "<Post:"+str(self.post_id)+">"
    
    def to_serializable_dict(self):
        """
        grabs the important data and returns it as a serizable dictionary
        """
        d = {
            "post_id": self.post_id,
            "timestamp": self.timestamp,
            "origin": self.origin,
            "content_type": self.content_type,
            "content_string": self.content_string,
            "source": self.source,
            "description": self.description,
            # "reference": self.reference, 
            #"signature": self.signature,
            "tags": [ t.tag for t in self.tags ] 
        }
        
        return d

 
class image_post(post):
    __mapper_args__ = {'polymorphic_identity': "image"}

    def __init__(self, image_url, thumb_url, origin=None, post_id=None, timestamp=None, source=None, description=None, reference=None, signature=None, tags=[]):
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

        __mapper_args__ = {'polymorphic_identity': "image"}

    def downcast(self):
        """
        wat.
        """
        self.image_url = self.content_string.split(';')[0]
        self.thumb_url = self.content_string.split(';')[1]
        return self
    
class tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String)
    posts = relationship('post', secondary=post_tag, backref='tag')
   
    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return "< Tag \""+self.tag+"\">"
    
    def __repr__(self):
        return self.__str__()
