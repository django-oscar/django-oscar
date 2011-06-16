from django.contrib import admin
from django.db.models import get_model

class DiscountOfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value', 'num_products')
    list_filter = ('discount_type',)

admin.site.register(get_model('discount', 'discountoffer'), DiscountOfferAdmin)
