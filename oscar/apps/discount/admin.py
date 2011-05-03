from django.contrib import admin

from oscar.core.loading import import_module
import_module('discount.models', ['DiscountOffer'], locals())

class DiscountOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value', 'num_products')
    list_filter = ('discount_type',)

admin.site.register(DiscountOffer, DiscountOfferAdmin)
