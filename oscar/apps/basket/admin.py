from django.contrib import admin
from django.db.models import get_model

Line = get_model('basket', 'line')


class LineInline(admin.TabularInline):
    model = Line


class BasketAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'status', 'num_lines', 'total_incl_tax',
                    'contains_a_voucher', 'date_created', 'date_submitted',
                    'time_before_submit')
    read_only_fields = ('date_merged', 'date_submitted')
    inlines = [LineInline]


admin.site.register(get_model('basket', 'basket'), BasketAdmin)
admin.site.register(Line)
admin.site.register(get_model('basket', 'LineAttribute'))
