import itertools

from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django_dynamic_fixture import get

from oscar.test import ClientTestCase
from oscar.apps.catalogue.models import Product, ProductClass
from oscar.apps.partner.models import StockRecord
from oscar.apps.catalogue.notification.models import ProductNotification


class TestANotificationForARegisteredUser(TestCase):

    def setUp(self):
        self.product = get(Product)
        self.user = get(User)
        self.notification = ProductNotification.objects.create(
            user=self.user,
            product=self.product)

    def test_uses_the_users_email_for_notifications(self):
        self.assertEquals(self.notification.get_notification_email(),
                          self.user.email)

    def test_defaults_to_inactive_status(self):
        self.assertFalse(self.notification.is_active())

    def test_defaults_to_unconfirmed(self):
        self.assertFalse(self.notification.is_confirmed())


class TestANotificationForAnAnonymousUser(TestCase):

    def setUp(self):
        self.product = get(Product)
        self.email = 'test@oscarcommerce.com'
        self.notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product)

    def test_users_specified_email_for_notifications(self):
        self.assertEquals(self.notification.get_notification_email(),
                          self.email)


class NotificationTestCase(ClientTestCase):
    product_counter = itertools.count()

    def create_product_class(self, name='books'):
        self.product_class = ProductClass.objects.create(name=name)

    def create_product(self):
        """
        Create a product of type book.
        """
        product_id = self.product_counter.next()

        product = get(Product, product_class=self.product_class,
                      title='product_%s' % product_id,
                      upc='00000000000%s' % product_id)

        get(StockRecord, product=product, num_in_stock=0)
        return product


class TestNotifyMeButtons(NotificationTestCase):

    def setUp(self):
        self.create_product_class()
        self.product = self.create_product()

    def test_are_displayed_on_unavailable_product_page(self):
        self.product.stockrecord.num_in_stock = 0
        self.product.stockrecord.save()

        url = reverse('catalogue:detail', args=(self.product.slug,
                                                self.product.id))
        response = self.client.get(url)

        self.assertContains(response, 'notify-me', status_code=200)

    def test_are_not_displayed_on_available_product_page(self):
        self.product.stockrecord.num_in_stock = 20
        self.product.stockrecord.save()

        url = reverse('catalogue:detail', args=(self.product.slug,
                                                self.product.id))
        response = self.client.get(url)
        self.assertNotContains(response, 'notify-me', status_code=200)

        self.product.stockrecord.num_in_stock = 1
        self.product.stockrecord.save()

        response = self.client.get(url)
        self.assertNotContains(response, 'notify-me', status_code=200)


class TestAnAnonymousUserRequestingANotification(NotificationTestCase):
    is_anonymous = True
    email = 'anonymous@email.com'

    def setUp(self):
        super(TestAnAnonymousUserRequestingANotification, self).setUp()
        self.create_product_class()
        self.product_1 = self.create_product()

    def test_creates_an_unconfirmed_notification_and_sends_confirmation_email(self):
        # Test creating a notification for an anonymous user. A notification
        # is generated for the user with confirmation and unsubscribe code.
        # The notification is set to UNCONFIRMED and a email is sent to the
        # user. The confirmation of the notification is handled by a link
        # that will activate the notification.
        notification_url = reverse('catalogue:notification-create',
                                   args=(self.product_1.slug,
                                         self.product_1.id))
        response = self.client.post(notification_url,
                                    data={'email': self.email},
                                    follow=True)

        self.assertContains(response, self.product_1.title, status_code=200)
        notification = ProductNotification.objects.get(email=self.email,
                                                       product=self.product_1)
        self.assertEquals(notification.status, ProductNotification.UNCONFIRMED)

        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue("confirm" in mail.outbox[0].body)
        self.assertTrue("unsubscribe" in mail.outbox[0].body)

    def test_can_activate_an_unconfirmed_notification(self):
        notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product_1)
        notification_url = reverse('catalogue:notification-confirm',
                                   args=(self.product_1.slug,
                                         self.product_1.id,
                                         notification.confirm_key,))
        self.client.get(notification_url)

        notification = ProductNotification.objects.get(pk=notification.id)
        self.assertEquals(notification.status, ProductNotification.ACTIVE)

    def test_can_unsubscribe_from_a_notification(self):
        # Test that unsubscribing from a notification inactivates the
        # notification. This does not delete the notification as it might be
        # used for analytical purposes later on by the site owner.
        notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product_1,
            status=ProductNotification.UNCONFIRMED
        )
        self.assertEquals(notification.status, ProductNotification.UNCONFIRMED)
        notification_url = reverse('catalogue:notification-unsubscribe',
                                   args=(self.product_1.slug,
                                         self.product_1.id,
                                         notification.unsubscribe_key,))
        self.client.get(notification_url)

        notification = ProductNotification.objects.get(pk=notification.id)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)


class TestARegisteredUserRequestingANotification(NotificationTestCase):
    is_anonymous = False
    is_staff = False
    email = 'testuser@oscar.com'

    def setUp(self):
        super(TestARegisteredUserRequestingANotification, self).setUp()
        self.create_product_class()
        self.product_1 = self.create_product()
        self.product_2 = self.create_product()

    def test_sees_email_on_product_page(self):
        product_url = reverse('catalogue:detail',
                              args=(self.product_1.slug, self.product_1.id))
        self.client.login()
        response = self.client.get(product_url)

        self.assertContains(response, self.email, status_code=200)

    def test_creates_a_notification_object(self):
        # Test creating a notification for an authenticated user with the
        # providing the account email address in the (hidden) signup form.
        self.assertEquals(self.user.notifications.count(), 0)
        self.client.login()

        notification_url = reverse('catalogue:notification-create',
                                   args=(self.product_1.slug,
                                          self.product_1.id))
        response = self.client.post(notification_url,
                                    data={'email': self.email},
                                    follow=True)

        self.assertContains(response, self.product_1.title, status_code=200)
        self.assertEquals(self.user.notifications.count(), 1)

        notification = self.user.notifications.all()[0]
        self.assertEquals(notification.get_notification_email(),
                          self.user.email)
        self.assertEquals(notification.confirm_key, None)
        self.assertEquals(notification.unsubscribe_key, None)

    def test_can_specify_an_alternative_email_address(self):
        # Test creating a notification with an email address that is different
        # from the user's account email. This should set the account email
        # address instead of the provided email in POST data.
        notification_url = reverse('catalogue:notification-create',
                              args=(self.product_1.slug, self.product_1.id))
        response = self.client.post(notification_url,
                                    data={'email': 'someother@oscar.com'},
                                    follow=True)

        self.assertContains(response, 'notified', status_code=200)

        self.assertEquals(self.user.notifications.count(), 1)

        notification = self.user.notifications.all()[0].productnotification
        self.assertEquals(notification.product.id, self.product_1.id)
        self.assertEquals(notification.get_notification_email(),
                          self.user.email)
        self.assertEquals(notification.confirm_key, None)
        self.assertEquals(notification.unsubscribe_key, None)

    def test_cannot_create_duplicate_notifications(self):
        # Test creating a notification when the user has already signed up for
        # this product notification. The user should be redirected to the product
        # page with a notification that he has already signed up.
        notification = get(ProductNotification, product=self.product_1,
                           user=self.user)
        notification_url = reverse('catalogue:notification-create',
                              args=(self.product_1.slug, self.product_1.id))
        response = self.client.post(notification_url,
                                    data={'email': self.user.email},
                                    follow=True)

        self.assertContains(response, self.product_1.title, status_code=200)
        self.assertEquals(self.user.notifications.count(), 1)
        self.assertEquals(notification,
                          self.user.notifications.all()[0].productnotification)


class TestAnAnonymousButExistingUserRequestingANotification(NotificationTestCase):
    is_anonymous = True
    email = 'testuser@oscar.com'
    username = 'testuser'
    password = 'password'

    def setUp(self):
        super(TestAnAnonymousButExistingUserRequestingANotification, self).setUp()
        self.create_user()
        self.create_product_class()
        self.product_1 = self.create_product()

    def test_gets_redirected_to_login_page(self):
        # Test creating a notification when a registered user is not yet logged
        # in. The email address in the form is checked against all users. If a
        # user profile has this email address set, the user will be redirected
        # to the login page and from there right back to the product detail
        # page where the user hits the 'Notify Me' button again.
        notification_url = reverse('catalogue:notification-create',
                                   args=(self.product_1.slug,
                                         self.product_1.id))
        response = self.client.post(notification_url,
                                    data={'email': self.email},
                                    follow=True)

        self.assertContains(response, 'Password', status_code=200)
        self.assertEquals(
            response.context[0].get('next'),
            reverse('catalogue:detail', args=(self.product_1.slug,
                                              self.product_1.id)))


class TestASignedInUser(NotificationTestCase):
    is_anonymous = False
    is_staff = False
    email = 'testuser@oscar.com'
    username = 'testuser'
    password = 'password'

    def setUp(self):
        super(TestASignedInUser, self).setUp()
        self.product_class = self.create_product_class()
        self.product = self.create_product()
        self.notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product,
            status=ProductNotification.ACTIVE)

    def test_can_deactivate_a_notification(self):
        self.assertEquals(self.notification.status, ProductNotification.ACTIVE)
        status_url = reverse('catalogue:notification-set-status',
                             args=(self.product.slug, self.product.id,
                                   self.notification.id,
                                   ProductNotification.INACTIVE))
        self.client.get(status_url)

        notification = ProductNotification.objects.get(pk=self.notification.id)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)

    def test_gets_a_404_when_accessing_invalid_url(self):
        self.assertEquals(self.notification.status, ProductNotification.ACTIVE)
        response = self.client.get(
            '/products/40-2/notify-me/set-status/1/invalid/')
        self.assertEquals(response.status_code, 404)

    def test_can_delete_a_notification(self):
        delete_url = reverse('catalogue:notification-delete',
                             args=(self.product.slug, self.product.id,
                                   self.notification.id))

        self.assertEquals(ProductNotification.objects.count(), 1)

        response = self.client.post(delete_url, data={'submit': 'submit'},
                                    follow=True)

        self.assertContains(response, '', status_code=200)
        self.assertEquals(ProductNotification.objects.count(), 0)


class TestNotificationEmails(TestCase):

    def setUp(self):
        self.product_class = ProductClass.objects.create(name='books')
        self.product = get(Product, product_class=self.product_class,
                           title='product_1', upc='000000000001')
        self.product_2 = get(Product, product_class=self.product_class,
                           title='product_2', upc='000000000002')

        self.user_1 = get(User, email='user@one.com')
        self.user_2 = get(User, email='user@two.com')

        get(StockRecord, product=self.product, num_in_stock=0)

    def test_are_not_sent_when_stock_level_remains_0(self):
        stock_record = StockRecord.objects.get(pk=1)
        self.assertEquals(stock_record.num_in_stock, 0)
        stock_record.save()
        self.assertEquals(stock_record.num_in_stock, 0)

        self.assertEquals(len(mail.outbox), 0)

    def test_are_not_sent_when_there_are_no_notifications(self):
        stock_record = StockRecord.objects.get(pk=1)
        self.assertEquals(stock_record.num_in_stock, 0)

        stock_record.num_in_stock = 20
        stock_record.save()

        self.assertEquals(len(mail.outbox), 0)

    def test_are_sent_correctly_when_there_are_notifications(self):
        ProductNotification.objects.create(user=self.user_1,
                                           product=self.product,
                                           status=ProductNotification.ACTIVE)
        ProductNotification.objects.create(user=self.user_2,
                                           product=self.product,
                                           status=ProductNotification.ACTIVE)
        ProductNotification.objects.create(user=None,
                                           email='anonymous@test.com',
                                           product=self.product,
                                           status=ProductNotification.ACTIVE)
        ProductNotification.objects.create(user=self.user_2,
                                           product=self.product_2,
                                           status=ProductNotification.ACTIVE)
        ProductNotification.objects.create(product=self.product,
                                           status=ProductNotification.INACTIVE)

        stock_record = StockRecord.objects.get(pk=1)
        self.assertEquals(stock_record.num_in_stock, 0)

        stock_record.num_in_stock = 20
        stock_record.save()

        self.assertEquals(len(mail.outbox), 3)
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.user_1.email, self.user_2.email, 'anonymous@test.com'],
        )

        notification = ProductNotification.objects.get(pk=1)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)
        self.assertNotEquals(notification.date_notified, None)

        notification = ProductNotification.objects.get(pk=2)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)
        self.assertNotEquals(notification.date_notified, None)

        notification = ProductNotification.objects.get(pk=3)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)
        self.assertNotEquals(notification.date_notified, None)

        notification = ProductNotification.objects.get(pk=4)
        self.assertEquals(notification.status, ProductNotification.ACTIVE)
        self.assertEquals(notification.date_notified, None)
