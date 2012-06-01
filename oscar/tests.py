from django.test import TestCase

from oscar.apps.address.tests import *
from oscar.apps.basket.tests import *
from oscar.apps.order.tests import *
from oscar.apps.catalogue.tests import *
from oscar.apps.partner.tests import *
from oscar.apps.checkout.tests import *
from oscar.apps.payment.tests import *
from oscar.apps.offer.tests import *
from oscar.apps.shipping.tests import *
from oscar.apps.customer.tests import *
from oscar.apps.promotions.tests import *
from oscar.apps.catalogue.reviews.tests import *
from oscar.apps.voucher.tests import *
from oscar.apps.partner.tests import *
from oscar.apps.dashboard.tests import *

from oscar.core.tests import *
from oscar.core.logging.tests import *

import oscar


class OscarTests(TestCase):

    def test_app_list_exists(self):
        core_apps = oscar.OSCAR_CORE_APPS
        self.assertTrue('oscar' in core_apps)

    def test_app_list_can_be_accessed_through_fn(self):
        core_apps = oscar.get_core_apps()
        self.assertTrue('oscar' in core_apps)

    def test_app_list_can_be_accessed_with_overrides(self):
        apps = oscar.get_core_apps(overrides=['apps.shipping'])
        self.assertTrue('apps.shipping' in apps)
        self.assertTrue('oscar.apps.shipping' not in apps)
