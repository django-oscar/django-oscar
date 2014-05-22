from django.contrib import admin

from oscar.apps.shipping.models import (
    OrderAndItemCharges, WeightBand, WeightBased)


class OrderChargesAdmin(admin.ModelAdmin):
    filter_horizontal = ('countries', )
    list_display = ('name', 'description', 'price_per_order', 'price_per_item',
                    'free_shipping_threshold')


class WeightBandInline(admin.TabularInline):
    model = WeightBand


class WeightBasedAdmin(admin.ModelAdmin):
    filter_horizontal = ('countries', )
    inlines = [WeightBandInline]


admin.site.register(OrderAndItemCharges, OrderChargesAdmin)
admin.site.register(WeightBased, WeightBasedAdmin)
