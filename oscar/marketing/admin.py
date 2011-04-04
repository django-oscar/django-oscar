from django.contrib import admin

from oscar.services import import_module
models = import_module('marketing.models', ['Banner'])

class BannerAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Banner, BannerAdmin)
