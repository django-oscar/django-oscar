import os
from PIL import Image as PImage

from django.core.files import File
from django.core.exceptions import FieldError

from oscar.core.loading import import_module
import_module('image.exceptions', ['ImageImportException', 'IdenticalImageException'], locals())
import_module('product.models', ['Item'], locals())
import_module('image.models', ['Image'], locals())


class Importer(object):
    
    allowed_extensions = ['.jpeg','.jpg','.gif','.png']
    
    def __init__(self, logger, field):
        self.logger = logger
        self._field = field
        
    def handle(self, dirname):
        stats = {
            'num_processed': 0,
            'num_skipped': 0,
            'num_invalid': 0         
        }
        for filename in self._get_image_files(dirname):
            try:
                lookup_value = self._get_lookup_value_from_filename(filename)
                self._process_image(dirname, filename, lookup_value)
                stats['num_processed'] += 1
            except Item.MultipleObjectsReturned:
                self.logger.warning("Multiple products matching %s='%s', skipping" % (self._field, lookup_value))
                stats['num_skipped'] += 1
            except Item.DoesNotExist:
                self.logger.warning("No item matching %s='%s'" % (self._field, lookup_value))
                stats['num_skipped'] += 1
            except IdenticalImageException:
                self.logger.warning(" - Identical image already exists for %s='%s', skipping" % (self._field, lookup_value))
                stats['num_skipped'] += 1
            except IOError:
                raise ImageImportException('%s is not a valid image' % filename)    
                stats['num_invalid'] += 1
            except FieldError, e:
                raise ImageImportException(e)
                self._process_image(dirname, filename)
        self.logger.info("Finished image import: %(num_processed)d imported, %(num_skipped)d skipped" % stats)
        
    def _get_image_files(self, dirname):
        filenames = []
        for filename in os.listdir(dirname):
            ext = os.path.splitext(filename)[1]
            if os.path.isfile(os.path.join(dirname, filename)) and ext in self.allowed_extensions:
                filenames.append(filename)
        return filenames
                
    def _process_image(self, dirname, filename, lookup_value):
        file_path = os.path.join(dirname, filename)
        trial_image = PImage.open(file_path)
        trial_image.verify()
        
        kwargs = {self._field: lookup_value}
        item = Item._default_manager.get(**kwargs)
        
        new_data = open(file_path).read()
        next_index = 0
        for existing in item.images.all():
            next_index = existing.display_order + 1
            if new_data == existing.original.read():
                raise IdenticalImageException()
            
        new_file = File(open(file_path))
        im = Image(product=item, display_order=next_index)
        im.original.save(filename, new_file, save=False)
        im.save()
        self.logger.info(' - Image added to "%s"' % item)
        
    def _fetch_item(self, filename):
        kwargs = {self._field: self._get_lookup_value_from_filename(filename)}
        return Item._default_manager.get(**kwargs)
    
    def _get_lookup_value_from_filename(self, filename):
        return os.path.splitext(filename)[0]
        