import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from oscar.apps.dashboard.vouchers import views
from oscar.core.loading import get_model
from oscar.test.factories import voucher
from oscar.test.factories.offer import ConditionalOfferFactory
from tests.fixtures import RequestFactory

ConditionalOffer = get_model("offer", "ConditionalOffer")
Voucher = get_model("voucher", "Voucher")
VoucherSet = get_model("voucher", "VoucherSet")


@pytest.fixture
def many_voucher_sets():
    voucher.VoucherSetFactory.create_batch(30)
    return VoucherSet.objects.all()


@pytest.mark.django_db
class TestDashboardVouchers:
    def test_voucher_update_view_for_voucher_in_set(self):
        vs = voucher.VoucherSetFactory(count=10)
        v = vs.vouchers.first()

        view = views.VoucherUpdateView.as_view()

        request = RequestFactory().get("/")
        response = view(request, pk=v.pk)
        assert response.status_code == 302
        assert response.url == reverse(
            "dashboard:voucher-set-update", kwargs={"pk": vs.pk}
        )
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "warning",
            "The voucher can only be edited as part of its set",
        )

        data = {
            "code": v.code,
            "name": "New name",
            "start_datetime": v.start_datetime,
            "end_datetime": v.end_datetime,
            "usage": v.usage,
            "offers": [v.offers],
        }
        request = RequestFactory().post("/", data=data)
        response = view(request, pk=v.pk)
        assert response.status_code == 302
        assert response.url == reverse(
            "dashboard:voucher-set-update", kwargs={"pk": vs.pk}
        )
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "warning",
            "The voucher can only be edited as part of its set",
        )
        v.refresh_from_db()
        assert v.name != "New name"

    def test_voucher_delete_view(self):
        v = voucher.VoucherFactory()
        v.offers.add(ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER))
        assert Voucher.objects.count() == 1
        assert ConditionalOffer.objects.count() == 1
        request = RequestFactory().post("/")
        response = views.VoucherDeleteView.as_view()(request, pk=v.pk)
        assert Voucher.objects.count() == 0
        # Related offer is not deleted
        assert ConditionalOffer.objects.count() == 1
        assert response.status_code == 302
        assert response.url == reverse("dashboard:voucher-list")
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "warning",
            "Voucher deleted",
        )

    def test_voucher_delete_view_for_voucher_in_set(self):
        vs = voucher.VoucherSetFactory(count=10)
        assert Voucher.objects.count() == 10
        request = RequestFactory().post("/")
        response = views.VoucherDeleteView.as_view()(request, pk=vs.vouchers.first().pk)
        vs.refresh_from_db()
        assert vs.count == 9  # "count" is updated
        assert Voucher.objects.count() == 9
        assert response.status_code == 302
        assert response.url == reverse(
            "dashboard:voucher-set-detail", kwargs={"pk": vs.pk}
        )
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "warning",
            "Voucher deleted",
        )


@pytest.mark.django_db
class TestDashboardVoucherSets:
    # pylint: disable=unused-argument, redefined-outer-name
    def test_voucher_set_list_view(self, rf, many_voucher_sets):
        view = views.VoucherSetListView.as_view()
        request = rf.get("/")
        response = view(request)
        # if these are missing the pagination is broken
        assert response.context_data["paginator"]
        assert response.context_data["page_obj"]
        assert response.status_code == 200

    def test_voucher_set_detail_view(self, rf):
        voucher.VoucherSetFactory(count=10)
        vs2 = voucher.VoucherSetFactory(count=15)
        request = rf.get("/")
        response = views.VoucherSetDetailView.as_view()(request, pk=vs2.pk)
        # The view should only list vouchers for vs2
        assert len(response.context_data["vouchers"]) == 15
        assert response.status_code == 200

    def test_voucher_set_delete_view(self):
        vs = voucher.VoucherSetFactory(count=10)
        assert VoucherSet.objects.count() == 1
        assert Voucher.objects.count() == 10
        request = RequestFactory().post("/")
        response = views.VoucherSetDeleteView.as_view()(request, pk=vs.pk)
        assert VoucherSet.objects.count() == 0
        assert Voucher.objects.count() == 0
        assert response.status_code == 302
        assert response.url == reverse("dashboard:voucher-set-list")
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "warning",
            "Voucher set deleted",
        )
