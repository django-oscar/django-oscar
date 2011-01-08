from django.contrib import admin
from sampleapp.payment.models import *

admin.site.register(Source)
admin.site.register(Transaction)
