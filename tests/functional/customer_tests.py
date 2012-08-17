import httplib
from mock import patch
from decimal import Decimal as D

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

from oscar.apps.customer.history_helpers import get_recently_viewed_product_ids
from oscar.test.helpers import create_product, create_order
from oscar.test import ClientTestCase, WebTestCase
from oscar.apps.basket.models import Basket


class HistoryHelpersTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.product = create_product()

    def test_viewing_product_creates_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertTrue('oscar_recently_viewed_products' in response.cookies)

    def test_id_gets_added_to_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        request = HttpRequest()
        request.COOKIES['oscar_recently_viewed_products'] = response.cookies['oscar_recently_viewed_products'].value
        self.assertTrue(self.product.id in get_recently_viewed_product_ids(request))


class AnonOrderDetail(TestCase):

    def setUp(self):
        self.client = Client()

    def test_404_received_for_unknown_order(self):
        response = self.client.get(reverse('customer:anon-order', kwargs={'order_number': 1000,
            'hash': '1231231232'}))
        self.assertEqual(httplib.NOT_FOUND, response.status_code)

    def test_200_received_for_order_with_correct_hash(self):
        order = create_order()
        response = self.client.get(reverse('customer:anon-order', kwargs={'order_number': order.number,
            'hash': order.verification_hash()}))
        self.assertEqual(httplib.OK, response.status_code)

    def test_404_received_for_order_with_incorrect_hash(self):
        order = create_order()
        response = self.client.get(reverse('customer:anon-order', kwargs={'order_number': order.number,
            'hash': 'bad'}))
        self.assertEqual(httplib.NOT_FOUND, response.status_code)


class EditProfileTests(TestCase):
    username = 'customer'
    password = 'cheeseshop'
    email = 'customer@example.com'

    def setUp(self):
        User.objects.create_user(username=self.username,
                                 email=self.email, password=self.password)
        is_successful = self.client.login(username=self.username,
                                          password=self.password)
        if not is_successful:
            self.fail("Unable to login as %s" % self.username)

    def tearDown(self):
        User.objects.all().delete()

    def test_update_profile_page_for_smoke(self):
        url = reverse('customer:profile-update')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertTrue('form' in response.context)


class AuthTestCase(TestCase):
    username = 'customer'
    password = 'cheeseshop'
    email = 'customer@example.com'

    def setUp(self):
        self.client = Client()
        self.product = create_product()
        User.objects.create_user(username=self.username,
                                 email=self.email, password=self.password)
        self.client.login(username=self.username, password=self.password)

    def test_cookies_deleted_on_logout(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertTrue('oscar_recently_viewed_products' in response.cookies)

        response = self.client.get(reverse('customer:logout'))
        self.assertTrue(('oscar_recently_viewed_products' not in response.cookies)
                        or not
                        self.client.cookies['oscar_recently_viewed_products'].coded_value)


class AuthStaffRedirectTests(TestCase):
    username = 'staff'
    password = 'cheeseshop'
    email = 'staff@example.com'

    def test_staff_member_login_for_dashboard(self):
        """
        Test if a staff member that is not yet logged in and trying to access the
        dashboard is redirected to the Oscar login page (instead of the ``admin``
        login page). Also test that the redirect after successful login will
        be the originally requested page.
        """
        self.client = Client()
        user = User.objects.create_user(username=self.username,
                                    email=self.email, password=self.password)
        user.is_staff = True
        user.save()

        response = self.client.get(reverse('dashboard:index'), follow=True)
        self.assertContains(response, "login-username", status_code=200)
        self.assertEquals(response.context['next'], reverse('dashboard:index'))


class ReorderTests(ClientTestCase):

    def test_can_reorder(self):
        order = create_order(user=self.user)
        Basket.objects.all().delete()

        self.client.post(reverse('customer:order',
                                            args=(order.number,)),
                                    {'order_id': order.pk,
                                     'action': 'reorder'})

        basket = Basket.objects.all()[0]
        self.assertEquals(len(basket.all_lines()), 1)

    def test_can_reorder_line(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]
        Basket.objects.all().delete()

        self.client.post(reverse('customer:order-line',
                                            args=(order.number, line.pk)),
                                    {'action': 'reorder'})

        basket = Basket.objects.all()[0]
        self.assertEquals(len(basket.all_lines()), 1)

    def test_cannot_reorder_out_of_stock_product(self):
        order = create_order(user=self.user)

        product = order.lines.all()[0].product
        product.stockrecord.num_in_stock = 0
        product.stockrecord.save()

        Basket.objects.all().delete()

        self.client.post(reverse('customer:order',
                                            args=(order.number,)),
                                    {'order_id': order.pk,
                                     'action': 'reorder'})

        basket = Basket.objects.all()[0]
        self.assertEquals(len(basket.all_lines()), 0)

    def test_cannot_reorder_out_of_stock_line(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]

        product = line.product
        product.stockrecord.num_in_stock = 0
        product.stockrecord.save()

        Basket.objects.all().delete()

        self.client.post(reverse('customer:order-line',
                                            args=(order.number, line.pk)),
                                    {'action': 'reorder'})

        basket = Basket.objects.all()[0]
        self.assertEquals(len(basket.all_lines()), 0)

    @patch('django.conf.settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD', 1)
    def test_cannot_reorder_when_basket_maximum_exceeded(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]

        Basket.objects.all().delete()
        #add a product
        product = create_product(price=D('12.00'))
        self.client.post(reverse('basket:add'), {'product_id': product.id,
                                                 'quantity': 1})


        basket = Basket.objects.all()[0]
        self.assertEquals(len(basket.all_lines()), 1)

        #try to reorder a product
        self.client.post(reverse('customer:order',
                                            args=(order.number,)),
                                    {'order_id': order.pk,
                                     'action': 'reorder'})

        self.assertEqual(len(basket.all_lines()), 1)
        self.assertNotEqual(line.product.pk, product.pk)

    @patch('django.conf.settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD', 1)
    def test_cannot_reorder_line_when_basket_maximum_exceeded(self):
        order = create_order(user=self.user)
        line = order.lines.all()[0]

        Basket.objects.all().delete()
        #add a product
        product = create_product(price=D('12.00'))
        self.client.post(reverse('basket:add'), {'product_id': product.id,
                                                 'quantity': 1})

        basket = Basket.objects.all()[0]
        self.assertEquals(len(basket.all_lines()), 1)

        self.client.post(reverse('customer:order-line',
                                            args=(order.number, line.pk)),
                                    {'action': 'reorder'})

        self.assertEquals(len(basket.all_lines()), 1)
        self.assertNotEqual(line.product.pk, product.pk)


class TestAnAnonymousUser(WebTestCase):

    def test_can_login(self):
        email, password = 'd@d.com', 'mypassword'
        User.objects.create_user('_', email, password)

        url = reverse('customer:login')
        form = self.app.get(url).forms['login_form']
        form['login-username'] = email
        form['login-password'] = password
        response = form.submit('login_submit')
        self.assertRedirectsTo(response, 'customer:summary')

    def test_can_register(self):
        url = reverse('customer:register')
        form = self.app.get(url).forms['register_form']
        form['registration-email'] = 'terry@boom.com'
        form['registration-password1'] = 'hedgehog'
        form['registration-password2'] = 'hedgehog'
        response = form.submit()
        self.assertRedirectsTo(response, 'customer:summary')


class TestASignedInUser(WebTestCase):

    def test_can_view_their_profile(self):
        email, password = 'd@d.com', 'mypassword'
        user = User.objects.create_user('_', email, password)
        url = reverse('customer:summary')
        self.app.get(url, user=user)
