from oscar.test.testcases import WebTestCase
from oscar.apps.customer.notifications import services
from oscar.test.factories import UserFactory
from django.utils.six.moves import http_client
from django.core.urlresolvers import reverse
from oscar.apps.customer.models import Notification

TEST_MSG_TEXT = "Test message with code 123x456c789"

class TestAUserWithUnreadNotifications(WebTestCase):

    def setUp(self):
        self.user = UserFactory()
        services.notify_user(self.user, TEST_MSG_TEXT)

    def test_can_see_them_in_page_header(self):
        homepage = self.app.get('/', user=self.user)
        self.assertTrue('num_unread_notifications' in homepage.context)
        self.assertEqual(1, homepage.context['num_unread_notifications'])

    def test_notification_list_is_not_mark_it_as_read(self):
        homepage = self.app.get('/', user=self.user)
        path = reverse('customer:notifications-inbox')
        response = self.app.get(path)
        self.assertEqual(http_client.OK, response.status_code)
        # number of notifications should not change if we visit the notification list
        self.assertEqual(1, homepage.context['num_unread_notifications'])

    def test_notification_mark_it_as_read(self):
        homepage = self.app.get('/', user=self.user)
        self.assertEqual(1, homepage.context['num_unread_notifications'])
        n = Notification.objects.get( subject = TEST_MSG_TEXT )
        path = reverse('customer:notifications-detail', kwargs={'pk': n.id} )
        response = self.app.get(path)
        self.assertEqual(http_client.OK, response.status_code)
        # number of notifications should not change if we visit the notification list
        self.assertEqual(0, homepage.context['num_unread_notifications'])