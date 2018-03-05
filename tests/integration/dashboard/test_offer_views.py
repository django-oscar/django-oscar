
import pytest

from oscar.apps.dashboard.offers import views as offer_views
from oscar.apps.dashboard.ranges import views as range_views
from oscar.core.loading import get_model
from oscar.test.factories import catalogue, offer

Range = get_model('offer', 'Range')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


@pytest.fixture
def many_ranges():
    for i in range(0, 30):
        offer.RangeFactory()
    return Range.objects.all()


@pytest.fixture
def many_offers():
    for i in range(0, 30):
        offer.ConditionalOfferFactory(
            name='Test offer %d' % i
        )


@pytest.fixture
def range_with_products():
    productrange = offer.RangeFactory()
    for i in range(0, 30):
        product = catalogue.ProductFactory()
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

    def test_range_product_list_view(self, rf, range_with_products):
        view = range_views.RangeProductListView.as_view()
        pk = range_with_products.pk

        request = rf.get('/')
        response = view(request, pk=pk)
        # if these are missing the pagination is broken
        assert response.context_data['paginator']
        assert response.context_data['page_obj']
        assert response.status_code == 200
