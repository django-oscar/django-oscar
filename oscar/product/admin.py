from oscar.product.models import AttributeType
from oscar.product.models import ItemType
from oscar.product.models import Item
from oscar.product.models import Attribute
from oscar.product.models import AttributeTypeMembership
from django.contrib import admin

class AttributeInline(admin.TabularInline):
    model = Attribute

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'partner_id', 'date_available', 'date_created', 'is_valid')
    inlines = [AttributeInline]


admin.site.register(AttributeType)
admin.site.register(AttributeTypeMembership)
admin.site.register(ItemType)
admin.site.register(Item, ItemAdmin)
admin.site.register(Attribute)
