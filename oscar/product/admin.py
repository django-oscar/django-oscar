from django.contrib import admin
from oscar.product.models import *

class AttributeInline(admin.TabularInline):
    model = ItemAttributeValue

class ItemClassAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    
class OptionInline(admin.TabularInline):
    model = Item.options.through    

class ItemAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'upc', 'get_item_class', 'is_top_level', 'is_group', 'is_variant', 'attribute_summary', 'date_created')
    prepopulated_fields = {"slug": ("title",)}
    inlines = [AttributeInline, OptionInline]

admin.site.register(ItemClass, ItemClassAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(AttributeType)
admin.site.register(ItemAttributeValue)
admin.site.register(Option)
