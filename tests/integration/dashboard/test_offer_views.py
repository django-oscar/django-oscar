import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from oscar.apps.dashboard.offers import views as offer_views
from oscar.apps.dashboard.ranges import views as range_views
from oscar.core.loading import get_model
from oscar.test.factories.catalogue import ProductFactory
from oscar.test.factories.offer import ConditionalOfferFactory, RangeFactory
from oscar.test.factories.voucher import VoucherFactory
from tests.fixtures import RequestFactory

Range = get_model('offer', 'Range')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


@pytest.fixture
def many_ranges():
    for i in range(0, 30):
        RangeFactory()
    return Range.objects.all()


@pytest.fixture
def many_offers():
    for i in range(0, 30):
        ConditionalOfferFactory(
            name='Test offer %d' % i
        )


@pytest.fixture
def range_with_products():
    productrange = RangeFactory()
    for i in range(0, 30):
        product = ProductFactory()
        productrange.add_product(product)
    return productrange


@pytest.mark.django_db
class TestDashboardOffers:

    def test_range_list_view(self, rf, many_ranges):
        request = rf.get('/')
        view = range_views.RangeListView.as_view()
        response = view(request)
        # if these are missing the pagination is broken
        assert response.context_data['paginator']
        assert response.context_data['page_obj']
        assert response.status_code == 200

    def test_offer_list_view(self, rf, many_offers):
        request = rf.get('/')
        view = offer_views.OfferListView.as_view()
        response = view(request)
        # if these are missing the pagination is broken
        assert response.context_data['paginator']
        assert response.context_data['page_obj']
        assert response.status_code == 200

    def test_offer_delete_view_for_voucher_offer_without_vouchers(self):
        offer = ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER)

        view = offer_views.OfferDeleteView.as_view()

        request = RequestFactory().get('/')
        response = view(request, pk=offer.pk)
        assert response.status_code == 200

        request = RequestFactory().post('/')
        response = view(request, pk=offer.pk)
        assert response.status_code == 302
        assert response.url == reverse('dashboard:offer-list')
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == ('success', "Offer deleted!")
        assert not ConditionalOffer.objects.exists()

    def test_offer_delete_view_for_voucher_offer_with_vouchers(self):
        offer = ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER)
        VoucherFactory().offers.add(offer)

        view = offer_views.OfferDeleteView.as_view()

        request = RequestFactory().get('/')
        response = view(request, pk=offer.pk)
        assert response.status_code == 302
        assert response.url == reverse('dashboard:offer-detail', kwargs={'pk': offer.pk})
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            'warning', "This offer can only be deleted if it has no vouchers attached to it")

        request = RequestFactory().post('/')
        response = view(request, pk=offer.pk)
        assert response.status_code == 302
        assert response.url == reverse('dashboard:offer-detail', kwargs={'pk': offer.pk})
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            'warning', "This offer can only be deleted if it has no vouchers attached to it")
        assert ConditionalOffer.objects.exists()

    def test_range_product_list_view(self, rf, range_with_products):
        view = range_views.RangeProductListView.as_view()
        pk = range_with_products.pk

        request = rf.get('/')
        response = view(request, pk=pk)
        # if these are missing the pagination is broken
        assert response.context_data['paginator']
        assert response.context_data['page_obj']
        assert response.status_code == 200
