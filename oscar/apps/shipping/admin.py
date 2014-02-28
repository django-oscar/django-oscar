from django.contrib import admin

from oscar.apps.shipping.models import (
    OrderAndItemCharges, WeightBand, WeightBased)


class OrderChargesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price_per_order', 'price_per_item',
                    'free_shipping_threshold')


class WeightBandAdmin(admin.ModelAdmin):
    list_display = ('method', 'weight_from', 'weight_to', 'charge')


admin.site.register(OrderAndItemCharges, OrderChargesAdmin)
admin.site.register(WeightBased)
admin.site.register(WeightBand, WeightBandAdmin)
