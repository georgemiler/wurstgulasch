from config import Configuration
import random
import time

# define base for database metadata
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from wtforms import Form, TextField

class identity(Base):
    __tablename__ = 'identity'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    wurstgulasch = Column(String)
    tagline = Column(String)
    bio = Column(String)
    avatar_url = Column(String)
    avatar_small_url = Column(String)

    def __init__(self, username, wurstgulasch=None, tagline='', bio=''):
        self.username = username
        if wurstgulasch is None:
            self.wurstgulasch = Configuration().base_domain
        else:
            self.wurstgulasch = wurstgulasch
        self.bio = bio
        self.tagline = tagline
        self.avatar_url = Configuration().base_url + "assets/default.png"
        self.avatar_small_url = Configuration().base_url + "assets/default.png"

user_friends = Table(
    'user_friends', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('friend_id', Integer, ForeignKey('identity.id'))
)


class user(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    passwordhash = Column(String)
    identity_id = Column(ForeignKey(identity.id))
    identity = relationship(identity, uselist=False)
    friends = relationship("identity", secondary=user_friends)

    def __init__(self, username, passwordhash, tagline='', bio=''):
        self.passwordhash = passwordhash
        self.identity = identity(username, tagline=tagline, bio=bio)

    def to_serializable_dict(self):
        return {
            'name': self.name,
            'tagline': self.tagline,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'avatar_small_url': self.avatar_small_url
        }

post_tag = Table(
    'post_tag', Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

post_reposters = Table(
    'post_reposters', Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('identity_id', Integer, ForeignKey('identity.id'))
)


class post(Base):
    __tablename__ = 'post'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer)
    timestamp = Column(Integer)
    owner_id = Column(Integer, ForeignKey(identity.id))
    owner = relationship("identity")
    content_type = Column('type', String)
    content_string = Column(String)
    reposters = relationship('identity', secondary=post_reposters,
                             backref='post')
    # TODO Tags as many to many relation
    tags = relationship('tag', secondary=post_tag, backref='post')
    # TODO reference as foreign key
    # signature = Column(String)

    # this one says that we want inherence in a single table and that
    # the column "content_type should define which one we are
    __mapper_args__ = {'polymorphic_on': content_type}

    def __init__(
        self, content_type, content_string, post_id=None, timestamp=None,
            origin=None, reference=None, signature=None, tags=[]):
        self.post_id = post_id or random.randint(1, 2 ** 32)
        self.timestamp = timestamp or int(time.time())
        self.content_type = content_type
        self.content_string = content_string
        # self.reference = reference
        # self.signature = signature

    def __str__(self):
        return "<Post:" + str(self.post_id) + ">"

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
            "tags": [t.tag for t in self.tags]
        }

        return d

    class BaseForm(Form):
        tags = TextField("Tags")


# include plugins
from contenttypes import *


class tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String)
    posts = relationship('post', secondary=post_tag, backref='tag')

    def __init__(self, tag):
        self.tag = tag

    def __str__(self):
        return "< Tag \"" + self.tag + "\">"

    def __repr__(self):
        return self.__str__()
