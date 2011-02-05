from django.contrib import admin

from oscar.basket.models import Basket, Line, LineAttribute

class BasketAdmin(admin.ModelAdmin):
    read_only_fields = ('date_merged', 'date_submitted')

admin.site.register(Basket, BasketAdmin)
admin.site.register(Line)
admin.site.register(LineAttribute)
