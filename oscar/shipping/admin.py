from django.contrib import admin

from oscar.services import import_module
models = import_module('shipping.models', ['OrderAndItemLevelChargeMethod'])

class MethodAdmin(admin.ModelAdmin):
    exclude = ('code',)
    list_display = ('name', 'description', 'price_per_order', 'price_per_item')

admin.site.register(models.OrderAndItemLevelChargeMethod, MethodAdmin)
