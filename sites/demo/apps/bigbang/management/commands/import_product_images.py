import os

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from PIL import Image

from oscar.apps.catalogue import models


class Command(BaseCommand):
    args = '/path/to/folder'
    help = 'For importing product images'

    def handle(self, *args, **options):
        if not args:
            directory = 'fixtures/images'
        else:
            directory = args[0]

        for filepath in self.image_filepaths(directory):
            self.import_image(filepath)

    def image_filepaths(self, directory):
        for filename in os.listdir(directory):
            yield os.path.join(directory, filename)

    def import_image(self, filepath):
        trial = Image.open(filepath)
        trial.verify()

        filename = os.path.basename(filepath)
        name, __ = os.path.splitext(filename)
        parts = name.split('_')
        upc = parts[0]
        if len(parts) > 1:
            order = int(parts[1])
        else:
            order = 0

        product = models.Product.objects.get(upc=upc)
        try:
            product_image = models.ProductImage.objects.get(
                product=product, display_order=order)
        except models.ProductImage.DoesNotExist:
            product_image = models.ProductImage(
                product=product, display_order=order)
        product_image.original.save(filename, File(open(filepath)), save=False)
        product_image.save()
