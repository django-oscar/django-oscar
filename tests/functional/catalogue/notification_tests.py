import itertools

from django.core import mail
from django.db.models import get_model
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import get

from webtest.app import AppError
from django_webtest import WebTest
from django_dynamic_fixture import get as G

from oscar.apps.catalogue.models import Product, ProductClass
from oscar.apps.partner.models import StockRecord
from oscar.apps.catalogue.notification.models import ProductNotification

Partner = get_model('partner', 'partner')


class NotificationWebTest(WebTest):
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

    def create_product_class(self, name='books'):
        self.product_class = ProductClass.objects.create(name=name)

    def create_product(self):
        product_id = self.product_counter.next()
        product = get(Product, product_class=self.product_class,
                      title='product_%s' % product_id,
                      upc='00000000000%s' % product_id, parent=None)

        G(StockRecord, product=product, num_in_stock=0)
        return product

    def get(self, *args, **kwargs):
        if self.user and not 'user' in kwargs:
            kwargs['user'] = self.user
        return self.app.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.user and not 'user' in kwargs:
            kwargs['user'] = self.user
        return self.app.post(*args, **kwargs)


class TestNotifyMeButtons(NotificationWebTest):

    def setUp(self):
        self.create_product_class()
        self.product = self.create_product()

    def test_are_displayed_on_unavailable_product_page(self):

        url = reverse('catalogue:detail', args=(self.product.slug,
                                                self.product.id))
        page = self.app.get(url)
        self.assertContains(page, 'notify-me', status_code=200)

    def test_are_not_displayed_on_available_product_page(self):
        self.product.stockrecord.num_in_stock = 20
        self.product.stockrecord.save()

        url = reverse('catalogue:detail', args=(self.product.slug,
                                                self.product.id))
        page = self.app.get(url)
        self.assertNotContains(page, 'notify-me', status_code=200)

        self.product.stockrecord.num_in_stock = 1
        self.product.stockrecord.save()

        page = self.app.get(url)
        self.assertNotContains(page, 'notify-me', status_code=200)


class TestAnAnonymousUserRequestingANotification(NotificationWebTest):
    is_anonymous = True
    email = 'anonymous@email.com'

    def setUp(self):
        super(TestAnAnonymousUserRequestingANotification, self).setUp()
        self.create_product_class()
        self.out_of_stock_product = self.create_product()

    def create_notification(self):
        page = self.get(reverse('catalogue:detail', args=(
            self.out_of_stock_product.slug,
            self.out_of_stock_product.id,
        )))
        notify_form = page.forms[1]
        notify_form['email'] = self.email
        return notify_form.submit()

    def test_submitting_an_invalid_email_redirects_back_to_page(self):
        page = self.get(reverse('catalogue:detail', args=(
            self.out_of_stock_product.slug,
            self.out_of_stock_product.id,
        )))
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


class TestARegisteredUserRequestingANotification(NotificationWebTest):
    is_anonymous = False
    email = 'testuser@oscar.com'

    def setUp(self):
        super(TestARegisteredUserRequestingANotification, self).setUp()
        self.create_product_class()
        self.product = self.create_product()

    def test_sees_email_on_product_page(self):
        product_url = reverse('catalogue:detail',
                              args=(self.product.slug, self.product.id))
        page = self.get(product_url)

        self.assertContains(page, self.email, status_code=200)

    def test_creates_a_notification_object(self):
        # Test creating a notification for an authenticated user with the
        # providing the account email address in the (hidden) signup form.
        self.assertEquals(self.user.product_notifications.count(), 0)

        page = self.get(reverse('catalogue:detail', args=(self.product.slug,
                                                          self.product.id)))
        notification_form = page.forms[1]
        notification_form['email'] = self.email
        page = notification_form.submit().follow()

        self.assertContains(page, self.product.title, status_code=200)
        self.assertEquals(self.user.product_notifications.count(), 1)

        notification = self.user.product_notifications.all()[0]
        self.assertEquals(notification.get_notification_email(),
                          self.user.email)
        self.assertEquals(notification.confirm_key, None)
        self.assertEquals(notification.unsubscribe_key, None)

    def test_can_specify_an_alternative_email_address(self):
        # Test creating a notification with an email address that is different
        # from the user's account email. This should set the account email
        # address instead of the provided email in POST data.
        page = self.get(reverse('catalogue:detail', args=(self.product.slug,
                                                          self.product.id)))
        notification_form = page.forms[1]
        notification_form['email'] = 'someother@oscar.com'
        page = notification_form.submit().follow()

        self.assertContains(page, 'notified', status_code=200)

        self.assertEquals(self.user.product_notifications.count(), 1)

        notification = self.user.product_notifications.all()[0]
        self.assertEquals(notification.product.id, self.product.id)
        self.assertEquals(notification.get_notification_email(),
                          self.user.email)
        self.assertEquals(notification.confirm_key, None)
        self.assertEquals(notification.unsubscribe_key, None)

    def test_cannot_create_duplicate_notifications(self):
        # Test creating a notification when the user has already signed up for
        # this product notification. The user should be redirected to the product
        # page with a notification that he has already signed up.
        get(ProductNotification, product=self.product, user=self.user)

        page = self.get(reverse('catalogue:detail', args=(self.product.slug,
                                                          self.product.id)))
        self.assertContains(
            page,
            "You will be notified when this product is available",
        )


class TestAnAnonymousButExistingUserRequestingANotification(NotificationWebTest):
    is_anonymous = True
    email = 'testuser@oscar.com'
    username = 'testuser'
    password = 'somerandompassword'

    def setUp(self):
        super(TestAnAnonymousButExistingUserRequestingANotification, self).setUp()
        User.objects.create(username=self.username, password=self.password,
                            email=self.email)
        self.create_product_class()
        self.product = self.create_product()

    def test_gets_redirected_to_login_page(self):
        # Test creating a notification when a registered user is not yet logged
        # in. The email address in the form is checked against all users. If a
        # user profile has this email address set, the user will be redirected
        # to the login page and from there right back to the product detail
        # page where the user hits the 'Notify Me' button again.
        product_url = reverse('catalogue:detail', args=(self.product.slug,
                                                        self.product.id))
        page = self.app.get(product_url)
        notification_form = page.forms[1]
        notification_form['email'] = self.email
        page = notification_form.submit()

        redirect_url = "%s?next=%s" % (reverse('customer:login'), product_url)
        self.assertRedirects(page, redirect_url)


class TestASignedInUser(NotificationWebTest):
    is_anonymous = False
    email = 'testuser@oscar.com'
    username = 'testuser'
    password = 'password'

    def setUp(self):
        super(TestASignedInUser, self).setUp()
        self.create_product_class()
        self.product = self.create_product()
        self.notification = ProductNotification.objects.create(
            user=self.user,
            product=self.product,
            status=ProductNotification.ACTIVE)

    def test_gets_a_404_when_accessing_invalid_url(self):
        self.assertEquals(self.notification.status, ProductNotification.ACTIVE)

        try:
            self.get('/products/40-2/notify-me/set-status/1/invalid/')
            self.fail('expected 404 but did not happen')
        except AppError:
            pass

    def test_can_deactivate_a_notification_from_the_account_section(self):
        self.assertEquals(self.notification.status, ProductNotification.ACTIVE)

        notification_tab_url = reverse('customer:summary')+"?tab=notifications"
        page = self.get(notification_tab_url)
        notification_form = page.forms[1]
        page = notification_form.submit('deactivate', index=0)

        self.assertRedirects(page, notification_tab_url)

        notification = ProductNotification.objects.get(id=self.notification.id)
        self.assertEquals(notification.status, ProductNotification.INACTIVE)
