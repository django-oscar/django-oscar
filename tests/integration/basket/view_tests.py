from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase
from django.utils import six

from oscar.apps.basket import views
from oscar.test.factories import BasketFactory, VoucherFactory
from oscar.test.utils import RequestFactory


class TestVoucherAddView(TestCase):
    def test_get(self):
        request = RequestFactory().get('/')

        view = views.VoucherAddView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 302)

    def _get_voucher_message(self, request):
        return '\n'.join(six.text_type(m.message) for m in get_messages(request))

    def test_post_valid(self):
        basket = BasketFactory()
        voucher = VoucherFactory()
        self.assertTrue(voucher.is_active())

        data = {
            'code': voucher.code
        }
        request = RequestFactory().post('/', data=data, basket=basket)

        view = views.VoucherAddView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

        voucher = voucher.__class__.objects.get(pk=voucher.pk)
        self.assertEqual(voucher.num_basket_additions, 1, msg=self._get_voucher_message(request))


class TestVoucherRemoveView(TestCase):

    def test_post_valid(self):
        basket = BasketFactory()
        voucher = VoucherFactory(num_basket_additions=5)
        basket.vouchers.add(voucher)

        data = {
            'code': voucher.code
        }
        request = RequestFactory().post('/', data=data, basket=basket)

        view = views.VoucherRemoveView.as_view()
        response = view(request, pk=voucher.pk)
        self.assertEqual(response.status_code, 302)

        voucher = voucher.__class__.objects.get(pk=voucher.pk)
        self.assertEqual(voucher.num_basket_additions, 4)
