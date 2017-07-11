from oscar.test.testcases import WebTestCase
from oscar.apps.customer.notifications import services
from oscar.test.factories import UserFactory


class TestAUserWithUnreadNotifications(WebTestCase):

    def setUp(self):
        self.user = UserFactory()
        services.notify_user(self.user, "Test message")

    def test_can_see_them_in_page_header(self):
        homepage = self.app.get('/', user=self.user)
        self.assertTrue('num_unread_notifications' in homepage.context)
        self.assertEqual(1, homepage.context['num_unread_notifications'])
