from django.contrib import admin

from oscar.services import import_module
models = import_module('discount.models', ['DiscountOffer'])

class DiscountOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value', 'num_products')

admin.site.register(models.DiscountOffer, DiscountOfferAdmin)
