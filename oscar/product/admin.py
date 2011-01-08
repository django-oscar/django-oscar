from django.contrib import admin
from oscar.product.models import *

class AttributeInline(admin.TabularInline):
    model = ItemAttributeValue

class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'is_canonical', 'get_attribute_summary', 'date_created')
    inlines = [AttributeInline]

admin.site.register(ItemType)
admin.site.register(Item, ItemAdmin)
admin.site.register(AttributeType)
admin.site.register(ItemAttributeValue)
