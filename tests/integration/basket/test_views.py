from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from oscar.apps.basket import views
from oscar.test import factories
from oscar.test.testcases import WebTestCase
from tests.fixtures import RequestFactory
from tests.functional.checkout import CheckoutMixin


class TestVoucherAddView(TestCase):
    def test_get(self):
        request = RequestFactory().get('/')

        view = views.VoucherAddView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 302)

    def _get_voucher_message(self, request):
        return '\n'.join(str(m.message) for m in get_messages(request))

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

    def test_post_valid_from_set(self):
        voucherset = factories.VoucherSetFactory()
        voucher = voucherset.vouchers.first()

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

        self.assertEqual(voucherset.num_basket_additions, 1)


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
        self.assertEqual(view.get_default_shipping_address(), user_address)

    def test_default_shipping_address_for_anonymous_user(self):
        request = RequestFactory().get(self.url)
        view = views.BasketView(request=request)
        self.assertIsNone(view.get_default_shipping_address())


class TestVoucherViews(CheckoutMixin, WebTestCase):
    csrf_checks = False

    def setUp(self):
        self.voucher = factories.create_voucher()
        super().setUp()

    def test_add_voucher(self):
        """
        Checks that voucher can be added to basket through appropriate view.
        """
        self.add_product_to_basket()

        assert self.voucher.basket_set.count() == 0

        response = self.post(reverse('basket:vouchers-add'), params={'code': self.voucher.code})
        self.assertRedirectsTo(response, 'basket:summary')
        assert self.voucher.basket_set.count() == 1

    def test_remove_voucher(self):
        """
        Checks that voucher can be removed from basket through appropriate view.
        """
        self.add_product_to_basket()
        self.add_voucher_to_basket(voucher=self.voucher)

        assert self.voucher.basket_set.count() == 1

        response = self.post(reverse('basket:vouchers-remove', kwargs={'pk': self.voucher.id}))
        self.assertRedirectsTo(response, 'basket:summary')
        assert self.voucher.basket_set.count() == 0
