from django.contrib import admin

from oscar.core.loading import import_module
models = import_module('basket.models', ['Basket', 'Line', 'LineAttribute'])


class BasketAdmin(admin.ModelAdmin):
    read_only_fields = ('date_merged', 'date_submitted')

admin.site.register(models.Basket, BasketAdmin)
admin.site.register(models.Line)
admin.site.register(models.LineAttribute)
