from product.models import AttributeType
from product.models import Type
from product.models import Item
from product.models import Attribute
from product.models import AttributeTypeMembership
from django.contrib import admin

class AttributeInline(admin.TabularInline):
    model = Attribute

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'partner_id', 'date_available', 'date_created', 'is_valid')
    inlines = [AttributeInline]


admin.site.register(AttributeType)
admin.site.register(AttributeTypeMembership)
admin.site.register(Type)
admin.site.register(Item, ItemAdmin)
admin.site.register(Attribute)
