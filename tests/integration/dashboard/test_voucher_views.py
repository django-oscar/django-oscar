import pytest

from oscar.apps.dashboard.vouchers import views
from oscar.core.loading import get_model
from oscar.test.factories import voucher

VoucherSet = get_model('voucher', 'VoucherSet')


@pytest.fixture
def many_voucher_sets():
    voucher.VoucherSetFactory.create_batch(30)
    return VoucherSet.objects.all()


@pytest.mark.django_db
class TestDashboardVoucherSets:

    def test_voucher_set_list_view(self, rf, many_voucher_sets):
        view = views.VoucherSetListView.as_view()
        request = rf.get('/')
        response = view(request)
        # if these are missing the pagination is broken
        assert response.context_data['paginator']
        assert response.context_data['page_obj']
        assert response.status_code == 200

    def test_voucher_set_detail_view(self, rf):
        voucher.VoucherSetFactory(count=10)
        vs2 = voucher.VoucherSetFactory(count=15)
        request = rf.get('/')
        response = views.VoucherSetDetailView.as_view()(request, pk=vs2.pk)
        # The view should only list vouchers for vs2
        assert len(response.context_data['vouchers']) == 15
        assert response.status_code == 200
