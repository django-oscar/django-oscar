import itertools

from django.test import TestCase
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

from django_dynamic_fixture import get

from oscar.test import ClientTestCase
from oscar.apps.catalogue.models import Product, ProductClass
from oscar.apps.partner.models import StockRecord 
from oscar.apps.catalogue.notification.models import ProductNotification


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

        stockrecord = get(StockRecord, product=product, num_in_stock=0)
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

    def setUp(self):
        super(self.__class__, self).setUp()
        self.create_product_class()
        self.product_1 = self.create_product()
        self.product_2 = self.create_product()

    def test_create_notification_for_anonymous_without_email(self):
        pass

    def test_create_notification_for_anonymous_with_email(self):
        pass


class CreateNotificationViewAsAuthenticatedUserTests(NotificationTestCase):
    is_anonymous = False
    is_staff = False
    email = 'testuser@oscar.com'

    def setUp(self):
        super(self.__class__, self).setUp()
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
        response = self.client.post(notification_url,
                                    data={'email': 'someother@oscar.com'},
                                    follow=True)

        product_url = reverse('catalogue:detail',
                               args=(self.product_1.slug, self.product_1.id))

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
        notification = get(ProductNotification, product=self.product_1, user=self.user,
                           )
        notification_url = reverse('catalogue:notification-add',
                              args=(self.product_1.slug, self.product_1.id))
        response = self.client.post(notification_url, data={'email': self.user.email},
                                    follow=True)

        self.assertContains(response, self.product_1.title, status_code=200)
        self.assertEquals(self.user.notifications.count(), 1)
        self.assertEquals(notification, self.user.notifications.all()[0])

   # def test_create_notification_authenticated_user(self):
   #     """
   #     This view will test notification creation from a authenticated user.
   #     - a user asks for notification
   #     - as she is authenticated, email is already verified and notification
   #     should be active
   #     """
   #     client = Client()
   #     loggedin = client.login(email=self.user.email,
   #                             username=self.user.username,
   #                             password=self.password)
   #     self.assertTrue(loggedin)

   #     response = client.get(self.product_1.get_absolute_url())
   #     self.assertEquals(response.status_code, 200)

   #     test_email = 'user@landmark.com'
   #     product_url = "/notify-me/%(slug)s-%(id)s/add/" % vars(self.product_1)
   #     response = client.post( product_url, { 'email': test_email })
   #     self.assertEquals(response.status_code, 302)

   #     notification = Notification.objects.get(user=self.user)
   #     product_set = notification.productnotification_set.filter(product=self.product_1)

   #     self.assertEquals(product_set.count(), 1)
   #     # should be activated by default as user is authenticated
   #     self.assertTrue(notification.active)
   #     # registered user shouln't be able to ask for notification in a different email
   #     self.assertEquals(notification.email, self.user.email)
   #     self.assertIsNotNone(notification.confirm_key)
   #     self.assertIsNotNone(notification.unsubscribe_key)


   # def test_create_notification_annonimous_user(self):
   #     """
   #         This test will make sure an unauthenticated user can subscribe
   #     for product notification.
   #     - An authenticated user is requested a email.
   #     - As he is an authenticated user, this notification has to be verified
   #     """
   #     annonymous_email = 'annonymous@landmark.com'
   #     client = Client()

   #     response = client.get(self.product_1.get_absolute_url())
   #     self.assertEquals(response.status_code, 200)

   #     product_url = "/notify-me/%(slug)s-%(id)s/add/" % vars(self.product_1)
   #     response = client.post(product_url, { 'email': annonymous_email })

   #     self.assertEquals(response.status_code, 302)

   #     notification = Notification.objects.get(email=annonymous_email)

   #     self.assertEquals(notification.user, None) # should be None as
   #     self.assertFalse(notification.active)   # should be false, needs to verify email

   #     # User needs to verify email
   #     confirm_url = '/notify-me/confirm/%s/' % notification.confirm_key
   #     response = client.get(confirm_url, {'email': annonymous_email})
   #     self.assertEquals(response.status_code, 200)
   #     notification = Notification.objects.get(email=annonymous_email)
   #     self.assertTrue(notification.active)

   #     self.assertIsNotNone(notification.confirm_key)
   #     self.assertIsNotNone(notification.unsubscribe_key)

   # def test_delete_notification_view(self):
   #     """
   #     """
   #     annonymous_email = "annonymous@landmark.com"
   #     notification = Notification.objects.create(active=True,
   #                                 email=annonymous_email,
   #                                 user=None,
   #                                 confirm_key='AAAAAAAAAAAAAAAA',
   #                                 unsubscribe_key='BBBBBBBBBBBBBBBB')

   #     client = Client()
   #     # User needs to verify email
   #     unsubscribe_url = '/notify-me/unsubscribe/%s/' % notification.unsubscribe_key
   #     response = client.get(unsubscribe_url, {'email': annonymous_email})
   #     self.assertEquals(response.status_code, 200)
   #     notification = Notification.objects.get(email=annonymous_email)
   #     self.assertFalse(notification.active)
