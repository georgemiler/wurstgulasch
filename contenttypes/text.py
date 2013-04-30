import sys
sys.path.append('..')

import os
import json

from model import post
from util import escape_html

from wtforms import Form, TextAreaField, validators

class Plugin(post):
    plugin_description = "Text"

    class CreatePostForm(post.BaseForm):
        text = TextAreaField("Description")

    __mapper_args__ = {'polymorphic_identity': "text"}

    def __init__(self, post_id=None, timestamp=None, text='', reference=None,
                 signature=None, tags=[]):
        plugin_specifics = {'text': text}
        post.__init__(self,
            post_id=post_id,
            timestamp=timestamp,
            content_type="text",
            content_string=json.dumps(plugin_specifics),
            reference=reference,
            signature=signature,
            tags=tags
        )
        plugin_specifics = json.loads(self.content_string)
        self.text = plugin_specifics['text']

    @classmethod
    def from_request(cls, form, request):
        # extract form data
        if not form.validate():
            pass
        else:
            text = cls(text = escape_html(form.text.data))
            return text

    def downcast(self):
        """
        wat.
        """
        plugin_specifics = json.loads(self.content_string)
        self.text = plugin_specifics['text']
        return self
