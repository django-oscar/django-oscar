# -*- coding: utf-8 -*-

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from oscar.core.loading import get_model

ProductImage = get_model('catalogue', 'ProductImage')
Category = get_model('catalogue', 'Category')


@receiver(post_save, sender=Category)
def denormalise_category_fields(sender, instance, **kwargs):
    instance.__class__.denormalise_fields()

if settings.OSCAR_DELETE_IMAGE_FILES:

    from django.db import models
    from django.db.models.signals import post_delete

    from sorl import thumbnail
    from sorl.thumbnail.helpers import ThumbnailError

    def delete_image_files(sender, instance, **kwargs):
        """
        Deletes the original image, created thumbnails, and any entries
        in sorl's key-value store.
        """
        image_fields = (models.ImageField, thumbnail.ImageField)
        for field in instance._meta.fields:
            if isinstance(field, image_fields):
                # Make Django return ImageFieldFile instead of ImageField
                fieldfile = getattr(instance, field.name)
                try:
                    thumbnail.delete(fieldfile)
                except ThumbnailError:
                    pass

    # connect for all models with ImageFields - add as needed
    models_with_images = [ProductImage, Category]
    for sender in models_with_images:
        post_delete.connect(delete_image_files, sender=sender)
