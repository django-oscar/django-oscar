from django.contrib import admin
from oscar.basket.models import *

admin.site.register(Basket)
admin.site.register(Line)
admin.site.register(LineAttribute)
