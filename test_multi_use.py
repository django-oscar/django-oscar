import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()
from oscar.test.factories import VoucherFactory, UserFactory, OrderFactory
from oscar.apps.voucher.models import Voucher
v = VoucherFactory(usage=Voucher.MULTI_USE)
u = UserFactory()
v.record_usage(OrderFactory(), u)
print("First usage recorded")
v.record_usage(OrderFactory(), u)
print("Second usage recorded")
