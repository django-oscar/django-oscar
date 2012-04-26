from django.core.urlresolvers import reverse

from oscar.test import ClientTestCase


class ViewTests(ClientTestCase):
    is_staff = True

    def test_pages_exist(self):
        urls = [reverse('dashboard:offer-list'),
                reverse('dashboard:offer-metadata'),
               ]
        for url in urls:
            self.assertIsOk(self.client.get(url))
