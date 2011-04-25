from django.contrib import admin

from oscar.core.loading import import_module
import_module('analytics.models', ['ProductRecord', 'UserRecord', 'UserSearch', 
                                    'UserProductView'], locals())

class ProductRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'num_views', 'num_basket_additions', 'num_purchases')
    
class UserProductViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'date_created')

class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'num_product_views', 'num_basket_additions', 'num_orders', 'total_spent', 'date_last_order')

admin.site.register(ProductRecord, ProductRecordAdmin)
admin.site.register(UserRecord, UserRecordAdmin)
admin.site.register(UserSearch)
admin.site.register(UserProductView, UserProductViewAdmin)
