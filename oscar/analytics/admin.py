from django.contrib import admin

from oscar.services import import_module
models = import_module('analytics.models', ['ProductRecord', 'UserRecord', 'UserSearch', 
                                            'UserProductView'])

class ProductRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'num_views', 'num_basket_additions', 'num_purchases')
    
class UserProductViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'date_created')

class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'num_product_views', 'num_basket_additions', 'num_orders', 'total_spent', 'date_last_order')

admin.site.register(models.ProductRecord, ProductRecordAdmin)
admin.site.register(models.UserRecord, UserRecordAdmin)
admin.site.register(models.UserSearch)
admin.site.register(models.UserProductView, UserProductViewAdmin)
