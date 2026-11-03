import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
os.environ["DATABASE_ENGINE"] = "django.db.backends.sqlite3"
django.setup()
from oscar.test.factories import VoucherFactory, UserFactory, OrderFactory
from oscar.apps.voucher.models import Voucher
try:
    v = VoucherFactory(usage=Voucher.MULTI_USE)
    u = UserFactory()
    v.record_usage(OrderFactory(), u)
    print("First usage recorded")
    v.record_usage(OrderFactory(), u)
    print("Second usage recorded")
except Exception as e:
    print(f"Error: {e}")
