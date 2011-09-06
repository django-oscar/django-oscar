from django.contrib import admin

from oscar.core.loading import import_module
import_module('voucher.models', ['Voucher', 'VoucherApplication'], locals())

    
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'usage', 'num_basket_additions', 'num_orders', 'total_discount')    
    readonly_fields = ('num_basket_additions', 'num_orders', 'total_discount')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'usage', 'start_date', 'end_date')
        }),
        ('Benefit', {
            'fields': ('offers',)
        }),
        ('Usage', {
            'fields': ('num_basket_additions', 'num_orders', 'total_discount')
        }),
        
    )
    
class VoucherApplicationAdmin(admin.ModelAdmin):
    list_display = ('voucher', 'user', 'order', 'date_created')
    readonly_fields = ('voucher', 'user', 'order')        


admin.site.register(Voucher, VoucherAdmin)
admin.site.register(VoucherApplication, VoucherApplicationAdmin)
