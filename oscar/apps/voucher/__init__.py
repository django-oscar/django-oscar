import django

from oscar.apps.voucher import receivers

default_app_config = 'oscar.apps.voucher.config.VoucherConfig'

if django.VERSION < (1.7):
    receivers.register()
