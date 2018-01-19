from oscar.test.testcases import WebTestCase
from oscar.apps.customer.notifications import services
from oscar.test.factories import UserFactory
from django.utils.six.moves import http_client
from django.core.urlresolvers import reverse

class TestAUserWithUnreadNotifications(WebTestCase):

    def setUp(self):
        self.user = UserFactory()
        services.notify_user(self.user, "Test message")

    def test_can_see_them_in_page_header(self):
        homepage = self.app.get('/', user=self.user)
        self.assertTrue('num_unread_notifications' in homepage.context)
        self.assertEqual(1, homepage.context['num_unread_notifications'])

        path = reverse('notifications-inbox:anon-order' )
        response = self.app.get(path)
        self.assertEqual(http_client.OK, response.status_code)
        # number of notifications should not change if we view the notofication list
        self.assertEqual(1, homepage.context['num_unread_notifications'])