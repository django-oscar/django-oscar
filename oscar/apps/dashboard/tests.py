from django.core.urlresolvers import reverse
from django.test import TestCase

from oscar.apps.dashboard.orders.tests import *
from oscar.apps.dashboard.reports.tests import *
from oscar.apps.dashboard.users.tests import *
from oscar.apps.dashboard.promotions.tests import *
from oscar.apps.dashboard.catalogue.tests import *
from oscar.apps.dashboard.pages.tests import *

from oscar.test import ClientTestCase


class AnonymousUserTests(ClientTestCase):

    def test_login_form_is_displayed_for_anon_user(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertTrue('Username' in response.content)


class DashboardViewTests(ClientTestCase):
    is_staff = True

    def test_dashboard_index_is_for_staff_only(self):
        urls = ('dashboard:index',
                'dashboard:order-list',
                'dashboard:users-index',)
        for name in urls:
            response = self.client.get(reverse(name))
            self.assertTrue('Password' not in response.content)
