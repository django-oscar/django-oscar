import os
import zlib
import tarfile
import zipfile
import tempfile
import shutil
from PIL import Image as PImage

from django.core.files import File
from django.core.exceptions import FieldError
from django.db.models import get_model

from oscar.core.loading import import_module
import_module('catalogue.exceptions', ['ImageImportError', 'IdenticalImageError', 'InvalidImageArchive'], locals())

Category = get_model('catalogue', 'category')
Product = get_model('catalogue', 'product')
ProductImage = get_model('catalogue', 'productimage')


def create_categories(bits):
    if len(bits) == 1:
        # Get or create root node
        try:
            root = Category.objects.get(depth=1, name=bits[0])
        except Category.DoesNotExist:
            root = Category.add_root(name=bits[0])
        return [root]
    else:
        parents = create_categories(bits[:-1])
        try:
            child = parents[-1].get_children().get(name=bits[-1])
        except Category.DoesNotExist:
            child = parents[-1].add_child(name=bits[-1])
        parents.append(child)
        return parents

def breadcrumbs_to_category(breadcrumbs, separator='>'):
    bits = [x.strip() for x in breadcrumbs.split(separator)]
    categories = create_categories(bits)
    return categories[-1]


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
        image_dir, filenames = self._get_image_files(dirname)
        if image_dir:
            for filename in filenames:
                try:
                    lookup_value = self._get_lookup_value_from_filename(filename)
                    self._process_image(image_dir, filename, lookup_value)
                    stats['num_processed'] += 1
                except Product.MultipleObjectsReturned:
                    self.logger.warning("Multiple products matching %s='%s', skipping" % (self._field, lookup_value))
                    stats['num_skipped'] += 1
                except Product.DoesNotExist:
                    self.logger.warning("No item matching %s='%s'" % (self._field, lookup_value))
                    stats['num_skipped'] += 1
                except IdenticalImageError:
                    self.logger.warning(" - Identical image already exists for %s='%s', skipping" % (self._field, lookup_value))
                    stats['num_skipped'] += 1
                except IOError, e:
                    raise ImageImportError('%s is not a valid image (%s)' % (filename, e))    
                    stats['num_invalid'] += 1
                except FieldError, e:
                    raise ImageImportError(e)
                    self._process_image(image_dir, filename)
            if image_dir != dirname:
                shutil.rmtree(image_dir)
        else:
            raise InvalidImageArchive('%s is not a valid image archive' % dirname)
        self.logger.info("Finished image import: %(num_processed)d imported, %(num_skipped)d skipped" % stats)
        
    def _get_image_files(self, dirname):
        filenames = []
        image_dir = self._extract_images(dirname)
        if image_dir:
            for filename in os.listdir(image_dir):
                ext = os.path.splitext(filename)[1]
                if os.path.isfile(os.path.join(image_dir, filename)) and ext in self.allowed_extensions:
                    filenames.append(filename)
        return image_dir, filenames

    def _extract_images(self, dirname):
        '''
        Returns path to directory containing images in dirname if successful.
        Returns empty string if dirname does not exist, or could not be opened.
        Assumes that if dirname is a directory, then it contains images.
        If dirname is an archive (tar/zip file) then the path returned is to a 
        temporary directory that should be deleted when no longer required.
        '''
        if os.path.isdir(dirname):
            return dirname        

        ext = os.path.splitext(dirname)[1]
        if ext in ['.gz', '.tar']:
            image_dir = tempfile.mkdtemp()
            try:
                tar_file = tarfile.open(dirname)
                tar_file.extractall(image_dir)
                tar_file.close()
                return image_dir
            except (tarfile.TarError, zlib.error):
                return ""
        elif ext == '.zip':
            image_dir = tempfile.mkdtemp()
            try:
                zip_file = zipfile.ZipFile(dirname)
                zip_file.extractall(image_dir) 
                zip_file.close()               
                return image_dir
            except (zlib.error, zipfile.BadZipfile, zipfile.LargeZipFile):
                return ""
        # unknown archive - perhaps this should be treated differently
        return ""
                
    def _process_image(self, dirname, filename, lookup_value):
        file_path = os.path.join(dirname, filename)
        trial_image = PImage.open(file_path)
        trial_image.verify()
        
        kwargs = {self._field: lookup_value}
        item = Product._default_manager.get(**kwargs)
        
        new_data = open(file_path).read()
        next_index = 0
        for existing in item.images.all():
            next_index = existing.display_order + 1
            try:
                if new_data == existing.original.read():
                    raise IdenticalImageError()
            except IOError:
                # File probably doesn't exist
                existing.delete()
            
        new_file = File(open(file_path))
        im = ProductImage(product=item, display_order=next_index)
        im.original.save(filename, new_file, save=False)
        im.save()
        self.logger.info(' - Image added to "%s"' % item)
        
    def _fetch_item(self, filename):
        kwargs = {self._field: self._get_lookup_value_from_filename(filename)}
        return Product._default_manager.get(**kwargs)
    
    def _get_lookup_value_from_filename(self, filename):
        return os.path.splitext(filename)[0]
        
