import itertools

from django.core import mail
from django.db.models import get_model
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import get

from django_webtest import WebTest
from django_dynamic_fixture import get as G

from oscar.test import ClientTestCase
from oscar.apps.catalogue.models import Product, ProductClass
from oscar.apps.partner.models import StockRecord
from oscar.apps.catalogue.notification.models import ProductNotification

Partner = get_model('partner', 'partner')


class CreatorMixin(object):

    def create_product_class(self, name='books'):
        self.product_class = ProductClass.objects.create(name=name)

    def create_product(self):
        product_id = self.product_counter.next()
        product = get(Product, product_class=self.product_class,
                      title='product_%s' % product_id,
                      upc='00000000000%s' % product_id, parent=None)

        G(StockRecord, product=product, num_in_stock=0)
        return product


class NotificationTestCase(ClientTestCase, CreatorMixin):
    product_counter = itertools.count()


class NotificationWebTest(WebTest, CreatorMixin):
    product_counter = itertools.count()
    username = 'testuser'
    password = 'somerandompassword'
    email = 'testuser@example.com'
    is_anonymous = True

    def setUp(self):
        self.user = None

        if not self.is_anonymous:
            self.user = User.objects.create(username=self.username,
                                            password=self.password,
                                            email=self.email)

    def get(self, *args, **kwargs):
        if self.user and not 'user' in kwargs:
            kwargs['user'] = self.user
        return self.app.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.user and not 'user' in kwargs:
            kwargs['user'] = self.user
        return self.app.post(*args, **kwargs)


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


class TestAnAnonymousUserRequestingANotification(NotificationWebTest):
    is_anonymous = True
    email = 'anonymous@email.com'

    def setUp(self):
        super(TestAnAnonymousUserRequestingANotification, self).setUp()
        self.create_product_class()
        self.out_of_stock_product = self.create_product()

    def create_notification(self):
        page = self.get(reverse('catalogue:index'))
        notify_form = page.forms[1]
        notify_form['email'] = self.email
        return notify_form.submit()

    def test_submitting_an_invalid_email_redirects_back_to_page(self):
        page = self.get(reverse('catalogue:index'))
        notify_form = page.forms[1]
        notify_form['email'] = u"invalid_email.com"
        page = notify_form.submit()

        self.assertContains(page, "Enter a valid e-mail address.")

    def test_creates_an_unconfirmed_notification_and_sends_confirmation_email(self):
        # Test creating a notification for an anonymous user. A notification
        # is generated for the user with confirmation and unsubscribe code.
        # The notification is set to UNCONFIRMED and a email is sent to the
        # user. The confirmation of the notification is handled by a link
        # that will activate the notification.
        self.create_notification()

        notifications = ProductNotification.objects.filter(email=self.email)
        self.assertEquals(notifications.count(), 1)

        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue("confirm" in mail.outbox[0].body)
        self.assertTrue("unsubscribe" in mail.outbox[0].body)


    def test_can_activate_an_unconfirmed_notification(self):
        self.test_creates_an_unconfirmed_notification_and_sends_confirmation_email()

        notification = ProductNotification.objects.get(email=self.email)
        product = notification.product

        self.assertEquals(notification.status, ProductNotification.UNCONFIRMED)

        page = self.get(notification.get_confirm_url())
        self.assertRedirects(
            page,
            reverse('catalogue:detail', args=(product.slug, product.id)),
            status_code=301
        )

        notification = ProductNotification.objects.get(id=notification.id)
        self.assertEquals(notification.status, ProductNotification.ACTIVE)

    def test_can_unsubscribe_from_a_notification(self):
        # Test that unsubscribing from a notification inactivates the
        # notification. This does not delete the notification as it might be
        # used for analytical purposes later on by the site owner.
        self.create_notification()

        notification = ProductNotification.objects.get(email=self.email)
        product = notification.product

        self.assertEquals(notification.status, ProductNotification.UNCONFIRMED)

        page = self.get(notification.get_unsubscribe_url())
        self.assertRedirects(
            page,
            reverse('catalogue:detail', args=(product.slug, product.id)),
            status_code=301
        )

        notification = ProductNotification.objects.get(email=self.email)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)


class TestARegisteredUserRequestingANotification(NotificationTestCase):
    is_anonymous = False
    is_staff = False
    email = 'testuser@oscar.com'

    def setUp(self):
        super(TestARegisteredUserRequestingANotification, self).setUp()
        self.create_product_class()
        self.product = self.create_product()
        #self.create_product()

    def test_sees_email_on_product_page(self):
        product_url = reverse('catalogue:detail',
                              args=(self.product.slug, self.product.id))
        self.client.login()
        response = self.client.get(product_url)

        self.assertContains(response, self.email, status_code=200)

    def test_creates_a_notification_object(self):
        # Test creating a notification for an authenticated user with the
        # providing the account email address in the (hidden) signup form.
        self.assertEquals(self.user.notifications.count(), 0)
        self.client.login()

        notification_url = reverse('catalogue:notification-create',
                                   args=(self.product.slug,
                                          self.product.id))
        response = self.client.post(notification_url,
                                    data={'email': self.email},
                                    follow=True)

        self.assertContains(response, self.product.title, status_code=200)
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
                              args=(self.product.slug, self.product.id))
        response = self.client.post(notification_url,
                                    data={'email': 'someother@oscar.com'},
                                    follow=True)

        self.assertContains(response, 'notified', status_code=200)

        self.assertEquals(self.user.notifications.count(), 1)

        notification = self.user.notifications.all()[0].productnotification
        self.assertEquals(notification.product.id, self.product.id)
        self.assertEquals(notification.get_notification_email(),
                          self.user.email)
        self.assertEquals(notification.confirm_key, None)
        self.assertEquals(notification.unsubscribe_key, None)

    def test_cannot_create_duplicate_notifications(self):
        # Test creating a notification when the user has already signed up for
        # this product notification. The user should be redirected to the product
        # page with a notification that he has already signed up.
        notification = get(ProductNotification, product=self.product,
                           user=self.user)
        notification_url = reverse('catalogue:notification-create',
                              args=(self.product.slug, self.product.id))
        response = self.client.post(notification_url,
                                    data={'email': self.user.email},
                                    follow=True)

        self.assertContains(response, self.product.title, status_code=200)
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
        self.product = self.create_product()

    def test_gets_redirected_to_login_page(self):
        # Test creating a notification when a registered user is not yet logged
        # in. The email address in the form is checked against all users. If a
        # user profile has this email address set, the user will be redirected
        # to the login page and from there right back to the product detail
        # page where the user hits the 'Notify Me' button again.
        notification_url = reverse('catalogue:notification-create',
                                   args=(self.product.slug,
                                         self.product.id))
        response = self.client.post(notification_url,
                                    data={'email': self.email},
                                    follow=True)

        self.assertContains(response, 'Password', status_code=200)
        self.assertEquals(
            response.context[0].get('next'),
            reverse('catalogue:detail', args=(self.product.slug,
                                              self.product.id)))


class TestASignedInUser(NotificationTestCase):
    is_anonymous = False
    is_staff = False
    email = 'testuser@oscar.com'
    username = 'testuser'
    password = 'password'

    def setUp(self):
        super(TestASignedInUser, self).setUp()
        self.create_product_class()
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

        notification = ProductNotification.objects.get(id=self.notification.id)
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
