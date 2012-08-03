from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G

from oscar.test import WebTestCase
from oscar.apps.catalogue.models import Product
from oscar.apps.catalogue.notification.models import ProductNotification
from oscar.apps.customer.notifications import services


class TestAUserWithUnreadNotifications(WebTestCase):

    def setUp(self):
        self.user = G(User)
        services.notify_user(self.user, "Test message")

    def test_can_see_them_in_page_header(self):
        homepage = self.app.get('/', user=self.user)
        self.assertTrue('num_unread_notifications' in homepage.context)
        self.assertEqual(1, homepage.context['num_unread_notifications'])


class TestChangingNotificationStatusByUser(WebTestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser',
                                        password='something',
                                        email='testuser@example.com')

        product = G(Product)
        self.notification1 = ProductNotification.objects.create(user=self.user,
                                                               product=product,
                                                               status='active')
        self.notification2 = ProductNotification.objects.create(user=self.user,
                                                               product=product,
                                                               status='inactive')

    def test_deactivating_an_active_product_notification(self):
        self.assertEquals(self.notification1.status, ProductNotification.ACTIVE)
        self.assertEquals(self.notification2.status, ProductNotification.INACTIVE)

        page = self.app.get(reverse("customer:summary"),
                            params={'tab': 'notification'}, user=self.user)
        notification_form = page.forms[1]
        notification_form.submit('deactivate', index=0)

        notification = ProductNotification.objects.get(pk=self.notification1.id)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)

        notification = ProductNotification.objects.get(pk=self.notification2.id)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)

    def test_activating_an_inactive_product_notification(self):
        self.assertEquals(self.notification1.status, ProductNotification.ACTIVE)
        self.assertEquals(self.notification2.status, ProductNotification.INACTIVE)

        page = self.app.get(reverse("customer:summary"),
                            params={'tab': 'notification'}, user=self.user)
        notification_form = page.forms[1]
        notification_form.submit('activate', index=0)

        notification = ProductNotification.objects.get(pk=self.notification2.id)
        self.assertEquals(notification.status, ProductNotification.ACTIVE)

        notification = ProductNotification.objects.get(pk=self.notification1.id)
        self.assertEquals(notification.status, ProductNotification.ACTIVE)
