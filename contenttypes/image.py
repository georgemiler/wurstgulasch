import sys
sys.path.append('..')

import os
from hashlib import md5
from PIL import Image
from StringIO import StringIO


from config import Configuration
from model import post
from util import check_mimetype, generate_thumbnail

from wtforms import Form, FileField, TextField, validators

class Plugin(post):
    plugin_description = "Image (Upload)"

    class CreatePostForm(Form):
        image = FileField("Image")
        description = TextField("Description")
        description = TextField("Description")
        source = TextField("Source")

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
    
    @classmethod
    def from_request(cls,request):
        # extract form data
        form = cls.CreatePostForm(request.form) 
        if not form.validate():
            pass
        else:
            c = Configuration()

            # -- store image --
            file_obj = request.files.get('image')
        
            # check mimetype
            mimetype = file_obj.content_type
            filetype = check_mimetype(mimetype, ["image"], ["jpeg", "png", "gif", "tiff"])

            # read image
            buf_image = file_obj.read()
            image = Image.open(StringIO(buf_image))
            thumbnail = generate_thumbnail(image, 300)

            # assemble filenames
            assetspath = os.path.join(c.base_path, 'assets')
            filename = md5(buf_image).hexdigest()+'.'+filetype
            imagepath = os.path.join(assetspath, filename)
            thumbpath = os.path.join(assetspath, 'thumb_'+filename)

            # write images
            image.save(imagepath)
            thumbnail.save(thumbpath)

            # generate image URLs
            image_url = c.base_url+'assets/'+filename          
            thumb_url = c.base_url+'assets/thumb_'+filename

            # -- assemble post --
            image_post = cls(
                image_url = image_url,
                thumb_url = thumb_url,
                source = form.source.data,
                description = form.description.data                 
            )
            
            return image_post

    def downcast(self):
        """
        wat.
        """
        self.image_url = self.content_string.split(';')[0]
        self.thumb_url = self.content_string.split(';')[1]
        return self
