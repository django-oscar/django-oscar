from django.contrib import admin

from oscar.services import import_module
models = import_module('marketing.models', ['Banner', 'Pod'])

class BannerAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'name']

class PodAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'page_position', 'name']

admin.site.register(models.Banner, BannerAdmin)
admin.site.register(models.Pod, PodAdmin)
