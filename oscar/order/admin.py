from django.contrib import admin
from oscar.order.models import *

admin.site.register(Order)
admin.site.register(BillingAddress)
admin.site.register(Batch)
admin.site.register(DeliveryAddress)
admin.site.register(BatchItem)
