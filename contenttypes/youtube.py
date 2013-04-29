import sys
sys.path.append('..')

import re
import os
import json
from hashlib import md5
from PIL import Image
from StringIO import StringIO


from config import Configuration
from model import post
from util import check_mimetype, generate_thumbnail

from wtforms import Form, TextAreaField, validators

class Plugin(post):
    plugin_description = "Youtube"

    class CreatePostForm(post.BaseForm):
        video_url = TextAreaField("Youtube-URL")

    __mapper_args__ = {'polymorphic_identity': "youtube"}

    def __init__(self, post_id=None, timestamp=None, video_id='', reference=None,
                 signature=None, tags=[]):
        plugin_specifics = {'video_id': video_id}
        post.__init__(self,
            post_id=post_id,
            timestamp=timestamp,
            content_type="youtube",
            content_string=json.dumps(plugin_specifics),
            reference=reference,
            signature=signature,
            tags=tags
        )
        plugin_specifics = json.loads(self.content_string)
        self.video_id = plugin_specifics['video_id']

    @classmethod
    def from_request(cls, form, request):
        # extract form data
        if not form.validate():
            pass
        else:
            # -- assemble post --
            video_url = form.video_url.data
            video_id = re.findall('(v=|youtu\.be/)(.*)&?', video_url)[0][1]
            post = cls(video_id = video_id)


            return post

    def downcast(self):
        """
        wat.
        """
        plugin_specifics = json.loads(self.content_string)
        self.video_id = plugin_specifics['video_id']
        return self
