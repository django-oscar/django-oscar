from django.test import TestCase
from django.test import Client

from django.contrib.auth.models import User

from landmark.catalogue.models import Product
from landmark.catalogue.models import ProductClass

from landmark.catalogue.notification.models import Notification


class CreateNotificationViewTest(TestCase):
    """

    """

    def _create_products(self):
        """
        This method will create a couple of random products
        """
        self.books_class = ProductClass.objects.create(name='books')
        for x in range(0, 5):
            setattr(self, 'product_%s' % x, Product.objects.create(
                                            product_class=self.books_class,
                                            title='product_%s' % x,
                                            landmark_id='LM000000%s' % x,
                                            upc='00000000000%s' % x
                ))

    def setUp(self):
        """
        """
        self.password = 'password'
        self.username = 'test'
        self.email = 'test@landmark.com'
        self.user = User.objects.create(username=self.username,
                                        email=self.email,
                                        is_active=True)
        self.user.save()
        self.user.set_password(self.password)
        self.user.save()
        # create a couple of products
        self._create_products()


    def test_create_notification_authenticated_user(self):
        """
        This view will test notification creation from a authenticated user.
        - a user asks for notification
        - as she is authenticated, email is already verified and notification
        should be active
        """
        client = Client()
        loggedin = client.login(email=self.user.email,
                                username=self.user.username,
                                password=self.password)
        self.assertTrue(loggedin)

        response = client.get(self.product_1.get_absolute_url())
        self.assertEquals(response.status_code, 200)

        test_email = 'user@landmark.com'
        product_url = "/notify-me/%(slug)s-%(id)s/add/" % vars(self.product_1)
        response = client.post( product_url, { 'email': test_email })
        self.assertEquals(response.status_code, 302)

        notification = Notification.objects.get(user=self.user)
        product_set = notification.productnotification_set.filter(product=self.product_1)

        self.assertEquals(product_set.count(), 1)
        # should be activated by default as user is authenticated
        self.assertTrue(notification.active)
        # registered user shouln't be able to ask for notification in a different email
        self.assertEquals(notification.email, self.user.email)
        self.assertIsNotNone(notification.confirm_key)
        self.assertIsNotNone(notification.unsubscribe_key)


    def test_create_notification_annonimous_user(self):
        """
            This test will make sure an unauthenticated user can subscribe
        for product notification.
        - An authenticated user is requested a email.
        - As he is an authenticated user, this notification has to be verified
        """
        annonymous_email = 'annonymous@landmark.com'
        client = Client()

        response = client.get(self.product_1.get_absolute_url())
        self.assertEquals(response.status_code, 200)

        product_url = "/notify-me/%(slug)s-%(id)s/add/" % vars(self.product_1)
        response = client.post(product_url, { 'email': annonymous_email })

        self.assertEquals(response.status_code, 302)

        notification = Notification.objects.get(email=annonymous_email)

        self.assertEquals(notification.user, None) # should be None as
        self.assertFalse(notification.active)   # should be false, needs to verify email

        # User needs to verify email
        confirm_url = '/notify-me/confirm/%s/' % notification.confirm_key
        response = client.get(confirm_url, {'email': annonymous_email})
        self.assertEquals(response.status_code, 200)
        notification = Notification.objects.get(email=annonymous_email)
        self.assertTrue(notification.active)

        self.assertIsNotNone(notification.confirm_key)
        self.assertIsNotNone(notification.unsubscribe_key)

    def test_delete_notification_view(self):
        """
        """
        annonymous_email = "annonymous@landmark.com"
        notification = Notification.objects.create(active=True,
                                    email=annonymous_email,
                                    user=None,
                                    confirm_key='AAAAAAAAAAAAAAAA',
                                    unsubscribe_key='BBBBBBBBBBBBBBBB')

        client = Client()
        # User needs to verify email
        unsubscribe_url = '/notify-me/unsubscribe/%s/' % notification.unsubscribe_key
        response = client.get(unsubscribe_url, {'email': annonymous_email})
        self.assertEquals(response.status_code, 200)
        notification = Notification.objects.get(email=annonymous_email)
        self.assertFalse(notification.active)


