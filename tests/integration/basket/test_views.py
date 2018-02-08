from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import six

from oscar.apps.basket import views
from oscar.test import factories
from tests.fixtures import RequestFactory


class TestVoucherAddView(TestCase):
    def test_get(self):
        request = RequestFactory().get('/')

        view = views.VoucherAddView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 302)

    def _get_voucher_message(self, request):
        return '\n'.join(six.text_type(m.message) for m in get_messages(request))

    def test_post_valid(self):
        voucher = factories.VoucherFactory()
        self.assertTrue(voucher.is_active())

        data = {
            'code': voucher.code
        }
        request = RequestFactory().post('/', data=data)
        request.basket.save()

        view = views.VoucherAddView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

        voucher = voucher.__class__.objects.get(pk=voucher.pk)
        self.assertEqual(voucher.num_basket_additions, 1, msg=self._get_voucher_message(request))


class TestVoucherRemoveView(TestCase):
    def test_post_valid(self):
        voucher = factories.VoucherFactory(num_basket_additions=5)

        data = {
            'code': voucher.code
        }
        request = RequestFactory().post('/', data=data)
        request.basket.save()
        request.basket.vouchers.add(voucher)

        view = views.VoucherRemoveView.as_view()
        response = view(request, pk=voucher.pk)
        self.assertEqual(response.status_code, 302)

        voucher = voucher.__class__.objects.get(pk=voucher.pk)
        self.assertEqual(voucher.num_basket_additions, 4)

    def test_post_with_missing_voucher(self):
        """ If the voucher is missing, verify the view queues a message and redirects. """
        pk = '12345'
        view = views.VoucherRemoveView.as_view()
        request = RequestFactory().post('/')
        request.basket.save()
        response = view(request, pk=pk)

        self.assertEqual(response.status_code, 302)

        actual = list(get_messages(request))[-1].message
        expected = "No voucher found with id '{}'".format(pk)
        self.assertEqual(actual, expected)


class TestBasketSummaryView(TestCase):
    def setUp(self):
        self.url = reverse('basket:summary')
        self.country = factories.CountryFactory()
        self.user = factories.UserFactory()

    def test_default_shipping_address(self):
        user_address = factories.UserAddressFactory(
            country=self.country, user=self.user, is_default_for_shipping=True
        )
        request = RequestFactory().get(self.url, user=self.user)
        view = views.BasketView(request=request)
        self.assertEquals(view.get_default_shipping_address(), user_address)

    def test_default_shipping_address_for_anonymous_user(self):
        request = RequestFactory().get(self.url)
        view = views.BasketView(request=request)
        self.assertIsNone(view.get_default_shipping_address())
