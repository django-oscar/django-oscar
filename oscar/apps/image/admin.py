from django.contrib import admin

from oscar.core.loading import import_module
import_module('image.models', ['Image'], locals())

admin.site.register(Image)
