from django.contrib import admin
from django.db.models import get_model

class UserAddressAdmin(admin.ModelAdmin):
    exclude = ('search_text', 'hash')
    readonly_fields = ('num_orders',)


admin.site.register(get_model('address', 'useraddress'), UserAddressAdmin)
admin.site.register(get_model('address', 'country'))
