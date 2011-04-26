from django.contrib import admin

from oscar.core.loading import import_module
import_module('basket.models', ['Basket', 'Line', 'LineAttribute'], locals())


class BasketAdmin(admin.ModelAdmin):
    read_only_fields = ('date_merged', 'date_submitted')


admin.site.register(Basket, BasketAdmin)
admin.site.register(Line)
admin.site.register(LineAttribute)
