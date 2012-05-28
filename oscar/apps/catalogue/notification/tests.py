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


class ProductNotificationTests(TestCase):

    def setUp(self):
        self.product = get(Product)

    def test_authenticated_user_notification_get_authenticated_email(self):
        user = get(User)
        notification = ProductNotification.objects.create(user=user, product=self.product)
        self.assertEquals(notification.get_notification_email(), user.email)

    def test_authenticated_user_notification_get_anonymous_email(self):
        notification = ProductNotification.objects.create(email='test@oscar.com',
                                                          product=self.product)

        self.assertEquals(notification.get_notification_email(),
                          'test@oscar.com')


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


class NotifyMeInViewTests(NotificationTestCase):

    def setUp(self):
        self.create_product_class()
        self.product = self.create_product()

    def test_notify_me_button_on_unavailable_product_page(self):
        self.product.stockrecord.num_in_stock = 0
        self.product.stockrecord.save()

        url = reverse('catalogue:detail', args=(self.product.slug, self.product.id))
        response = self.client.get(url)

        self.assertContains(response, 'notify-me', status_code=200)

    def test_notify_me_button_on_available_product_page(self):
        self.product.stockrecord.num_in_stock = 20
        self.product.stockrecord.save()

        url = reverse('catalogue:detail', args=(self.product.slug, self.product.id))
        response = self.client.get(url)
        self.assertNotContains(response, 'notify-me', status_code=200)

        self.product.stockrecord.num_in_stock = 1
        self.product.stockrecord.save()

        response = self.client.get(url)
        self.assertNotContains(response, 'notify-me', status_code=200)


class CreateNotificationViewAsAnonymousTests(NotificationTestCase):
    is_anonymous = True
    email = 'anonymous@email.com'

    def setUp(self):
        super(CreateNotificationViewAsAnonymousTests, self).setUp()
        self.create_product_class()
        self.product_1 = self.create_product()

    def test_create_notification_for_anonymous(self):
        """
        Test creating a notification for an anonymous user. A notification
        is generated for the user with confirmation and unsubscribe code.
        The notification is set to UNCONFIRMED and a email is sent to the
        user. The confirmation of the notification is handled by a link
        that will activate the notification.
        """
        notification_url = reverse('catalogue:notification-add',
                                   args=(self.product_1.slug, self.product_1.id))
        response = self.client.post(notification_url, data={'email': self.email},
                                    follow=True)

        self.assertContains(response, self.product_1.title, status_code=200)
        notification = ProductNotification.objects.get(email=self.email,
                                                       product=self.product_1)
        self.assertEquals(notification.status, ProductNotification.UNCONFIRMED)

        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue("confirm" in mail.outbox[0].body)
        self.assertTrue("unsubscribe" in mail.outbox[0].body)

    def test_activating_unconfirmed_notification(self):
        notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product_1
        )
        notification_url = reverse('catalogue:notification-confirm',
                                   args=(self.product_1.slug,
                                         self.product_1.id,
                                         notification.confirm_key,))
        self.client.get(notification_url)

        notification = ProductNotification.objects.get(pk=notification.id)
        self.assertEquals(notification.status, ProductNotification.ACTIVE)

    def test_unsubscribing_from_notification(self):
        """
        Test that unsubscribing from a notification inactivates the notification.
        This does not delete the notification as it might be used for
        analytical purposes later on by the site owner.
        """
        notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product_1
        )
        notification_url = reverse('catalogue:notification-unsubscribe',
                                   args=(self.product_1.slug,
                                         self.product_1.id,
                                         notification.unsubscribe_key,))
        self.client.get(notification_url)

        notification = ProductNotification.objects.get(pk=notification.id)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)


class CreateNotificationViewAsAuthenticatedUserTests(NotificationTestCase):
    is_anonymous = False
    is_staff = False
    email = 'testuser@oscar.com'

    def setUp(self):
        super(CreateNotificationViewAsAuthenticatedUserTests, self).setUp()
        self.create_product_class()
        self.product_1 = self.create_product()
        self.product_2 = self.create_product()

    def test_prefilled_email_for_authenticated_user(self):
        product_url = reverse('catalogue:detail',
                              args=(self.product_1.slug, self.product_1.id))
        self.client.login()
        response = self.client.get(product_url)

        self.assertContains(response, self.email, status_code=200)

    def test_create_notification_for_auth_user_with_email(self):
        """
        Test creating a notification for an authenticated user with the
        providing the account email address in the (hidden) signup form.
        """
        self.assertEquals(self.user.notifications.count(), 0)
        self.client.login()

        notification_url = reverse('catalogue:notification-add',
                                   args=(self.product_1.slug, self.product_1.id))
        response = self.client.post(notification_url, data={'email': self.email},
                                    follow=True)

        self.assertContains(response, self.product_1.title, status_code=200)
        self.assertEquals(self.user.notifications.count(), 1)

        notification = self.user.notifications.all()[0]
        self.assertEquals(notification.get_notification_email(), self.user.email)
        self.assertEquals(notification.confirm_key, None)
        self.assertEquals(notification.unsubscribe_key, None)

    def test_create_notification_for_auth_user_with_invalid_email(self):
        """
        Test creating a notification with an email address that is different
        from the user's account email. This should set the account email
        address instead of the provided email in POST data.
        """
        notification_url = reverse('catalogue:notification-add',
                              args=(self.product_1.slug, self.product_1.id))
        self.client.post(notification_url, data={'email': 'someother@oscar.com'},
                         follow=True)

        ## FIXME: this need template tag implementation
        #self.assertContains(response, 'You chose to be notified', status_code=200)

        self.assertEquals(self.user.notifications.count(), 1)

        notification = self.user.notifications.all()[0]
        self.assertEquals(notification.product.id, self.product_1.id)
        self.assertEquals(notification.get_notification_email(), self.user.email)
        self.assertEquals(notification.confirm_key, None)
        self.assertEquals(notification.unsubscribe_key, None)

    def test_create_notification_for_auth_user_when_notification_exists(self):
        """
        Test creating a notification when the user has already signed up for
        this product notification. The user should be redirected to the product
        page with a notification that he has already signed up.
        """
        notification = get(ProductNotification, product=self.product_1, user=self.user)
        notification_url = reverse('catalogue:notification-add',
                              args=(self.product_1.slug, self.product_1.id))
        response = self.client.post(notification_url, data={'email': self.user.email},
                                    follow=True)

        self.assertContains(response, self.product_1.title, status_code=200)
        self.assertEquals(self.user.notifications.count(), 1)
        self.assertEquals(notification, self.user.notifications.all()[0])


class CreateNotificationViewAsAnonymousUserTests(NotificationTestCase):
    is_anonymous = True
    email = 'testuser@oscar.com'
    username = 'testuser'
    password = 'password'

    def setUp(self):
        super(CreateNotificationViewAsAnonymousUserTests, self).setUp()
        self.create_user()

        self.create_product_class()
        self.product_1 = self.create_product()
        self.product_2 = self.create_product()

    def test_creating_notification_when_registered_user_is_not_logged_in(self):
        """
        Test creating a notification when a registered user is not yet logged
        in. The email address in the form is checked against all users. If a
        user profile has this email address set, the user will be redirected
        to the login page and from there right back to the product detail
        page where the user hits the 'Notify Me' button again.
        """
        notification_url = reverse('catalogue:notification-add',
                                   args=(self.product_1.slug, self.product_1.id))
        response = self.client.post(notification_url, data={'email': self.email},
                                    follow=True)

        self.assertContains(response, 'Password', status_code=200)
        self.assertEquals(
            response.context[0].get('next'),
            reverse('catalogue:detail', args=(self.product_1.slug,
                                              self.product_1.id))
        )


class SetStatusProductNotificationViewTests(NotificationTestCase):
    is_anonymous = False
    is_staff = False
    email = 'testuser@oscar.com'
    username = 'testuser'
    password = 'password'

    def setUp(self):
        super(SetStatusProductNotificationViewTests, self).setUp()
        self.product_class = self.create_product_class()
        self.product = self.create_product()
        self.notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product,
            status=ProductNotification.ACTIVE
        )

    def test_setting_notification_status_active(self):
        self.assertEquals(self.notification.status, ProductNotification.ACTIVE)
        status_url = reverse('catalogue:notification-set-status',
                             args=(self.product.slug, self.product.id,
                                   self.notification.id,
                                   ProductNotification.INACTIVE))

        response = self.client.get(status_url)

        notification = ProductNotification.objects.get(pk=self.notification.id)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)

    def test_setting_notification_status_with_invalid_status(self):
        self.assertEquals(self.notification.status, ProductNotification.ACTIVE)
        status_url = reverse('catalogue:notification-set-status',
                             args=(self.product.slug, self.product.id,
                                   self.notification.id,
                                   ProductNotification.INACTIVE))

        response = self.client.get('/products/40-2/notify-me/set-status/1/invalid/')

        self.assertEquals(response.status_code, 404)


class DeleteNotificationViewTests(NotificationTestCase):
    is_anonymous = False
    is_staff = True
    email = 'staff@oscar.com'
    username = 'staff'
    password = 'password'

    def setUp(self):
        super(DeleteNotificationViewTests, self).setUp()
        self.product_class = self.create_product_class()
        self.product = self.create_product()
        self.notification = ProductNotification.objects.create(
            email=self.email,
            product=self.product
        )

    def test_deleting_notification(self):
        delete_url = reverse('catalogue:notification-remove',
                             args=(self.product.slug, self.product.id,
                                   self.notification.id))

        self.assertEquals(ProductNotification.objects.count(), 1)

        response = self.client.post(delete_url, data={'submit': 'submit'},
                                    follow=True)

        self.assertContains(response, '', status_code=200)
        self.assertEquals(ProductNotification.objects.count(), 0)


class SendingNotificationTests(TestCase):

    def setUp(self):
        self.product_class = ProductClass.objects.create(name='books')
        self.product = get(Product, product_class=self.product_class,
                           title='product_1', upc='000000000001')
        self.product_2 = get(Product, product_class=self.product_class,
                           title='product_2', upc='000000000002')

        self.user_1 = get(User, email='user@one.com')
        self.user_2 = get(User, email='user@two.com')

        get(StockRecord, product=self.product, num_in_stock=0)

    def test_sending_email_with_empty_stock(self):
        stock_record = StockRecord.objects.get(pk=1)
        self.assertEquals(stock_record.num_in_stock, 0)
        stock_record.save()
        self.assertEquals(stock_record.num_in_stock, 0)

        self.assertEquals(len(mail.outbox), 0)

    def test_sending_email_without_notifications(self):
        stock_record = StockRecord.objects.get(pk=1)
        self.assertEquals(stock_record.num_in_stock, 0)

        stock_record.num_in_stock = 20
        stock_record.save()

        self.assertEquals(len(mail.outbox), 0)

    def test_sending_email_with_notifications(self):
        ProductNotification.objects.create(user=self.user_1,
                                           product=self.product,
                                           status=ProductNotification.ACTIVE)
        ProductNotification.objects.create(user=self.user_2,
                                           product=self.product,
                                           status=ProductNotification.ACTIVE)
        ProductNotification.objects.create(user=None, email='anonymous@test.com',
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
