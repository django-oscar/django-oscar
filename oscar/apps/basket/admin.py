from django.contrib import admin
from django.db.models import get_model


class BasketAdmin(admin.ModelAdmin):
    read_only_fields = ('date_merged', 'date_submitted')


admin.site.register(get_model('basket', 'basket'), BasketAdmin)
admin.site.register(get_model('basket', 'line'))
admin.site.register(get_model('basket', 'LineAttribute'))
