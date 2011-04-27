import os

from PIL import Image as PImage

from django.core.files import File
from django.core.exceptions import FieldError

from oscar.core.loading import import_module

import_module('image.exceptions', ['ImageImportException'], locals())
import_module('product.models', ['Item'], locals())
import_module('image.models', ['Image'], locals())

class Importer(object):
    
    def __init__(self, logger, field):
        self.logger = logger
        self._field = field
        
    def handle(self, filename, dirname):
        
        f = os.path.join(dirname,filename)
        
        kwargs = {}
        kwargs[self._field] = os.path.splitext(filename)[0]
        
        try:
            item = Item.objects.get(**kwargs)
            
            create_new = True
            max_index = 0
            
            new_data = open(f).read()
            
            trial_image = PImage.open(f)
            trial_image.verify()

            # if this image already exists for the Item, ignore it
            for existing in item.images.all():
                max_index = existing.display_order + 1
                if new_data == existing.original.read():
                    create_new = False
                    break
                
            if create_new:
                new_file = File(open(f))
                im = Image(product=item,display_order=max_index)
                im.original.save(filename, new_file, save=False)
                im.save()
                self.logger.info('image added to "%s"' % item)
        except IOError:
            raise ImageImportException('%s is not a valid image' % filename)
        except (Item.MultipleObjectsReturned, Item.DoesNotExist):
            pass # We don't care
        except FieldError, e:
            raise ImageImportException(e)