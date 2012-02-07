from django.core.urlresolvers import reverse

from oscar.test import ClientTestCase


class ViewTests(ClientTestCase):
    is_staff = True

    def test_list_page(self):
        url = reverse('dashboard:promotion-list')
        response = self.client.get(url)
        self.assertIsOk(response)