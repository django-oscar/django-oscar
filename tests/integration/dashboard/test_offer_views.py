# pylint: disable=redefined-outer-name, unused-argument
import json

import pytest
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from oscar.apps.dashboard.offers import views as offer_views
from oscar.apps.dashboard.ranges import views as range_views
from oscar.apps.offer.custom import create_benefit, create_condition
from oscar.core.loading import get_model
from oscar.test.factories.catalogue import ProductFactory
from oscar.test.factories.offer import ConditionalOfferFactory, RangeFactory
from oscar.test.factories.voucher import VoucherFactory
from tests._site.model_tests_app.models import CustomBenefitModel, CustomConditionModel
from tests.fixtures import RequestFactory

Range = get_model("offer", "Range")
ConditionalOffer = get_model("offer", "ConditionalOffer")
Benefit = get_model("offer", "Benefit")
Condition = get_model("offer", "Condition")


@pytest.fixture
def many_ranges():
    for _ in range(0, 30):
        RangeFactory()
    return Range.objects.all()


@pytest.fixture
def many_offers():
    for i in range(0, 30):
        ConditionalOfferFactory(name="Test offer %d" % i)


@pytest.fixture
def range_with_products():
    productrange = RangeFactory()
    for _ in range(0, 30):
        product = ProductFactory()
        productrange.add_product(product)
    return productrange


@pytest.mark.django_db
class TestDashboardOffers:
    def test_range_list_view(self, rf, many_ranges):
        request = rf.get("/")
        view = range_views.RangeListView.as_view()
        response = view(request)
        # if these are missing the pagination is broken
        assert response.context_data["paginator"]
        assert response.context_data["page_obj"]
        assert response.status_code == 200

    def test_offer_list_view(self, rf, many_offers):
        request = rf.get("/")
        view = offer_views.OfferListView.as_view()
        response = view(request)
        # if these are missing the pagination is broken
        assert response.context_data["paginator"]
        assert response.context_data["page_obj"]
        assert response.status_code == 200

    def test_offer_delete_view_for_voucher_offer_without_vouchers(self):
        offer = ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER)

        view = offer_views.OfferDeleteView.as_view()

        request = RequestFactory().get("/")
        response = view(request, pk=offer.pk)
        assert response.status_code == 200

        request = RequestFactory().post("/")
        response = view(request, pk=offer.pk)
        assert response.status_code == 302
        assert response.url == reverse("dashboard:offer-list")
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "success",
            "Offer deleted!",
        )
        assert not ConditionalOffer.objects.exists()

    def test_offer_delete_view_for_voucher_offer_with_vouchers(self):
        offer = ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER)
        VoucherFactory().offers.add(offer)

        view = offer_views.OfferDeleteView.as_view()

        request = RequestFactory().get("/")
        response = view(request, pk=offer.pk)
        assert response.status_code == 302
        assert response.url == reverse(
            "dashboard:offer-detail", kwargs={"pk": offer.pk}
        )
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "warning",
            "This offer can only be deleted if it has no vouchers attached to it",
        )

        request = RequestFactory().post("/")
        response = view(request, pk=offer.pk)
        assert response.status_code == 302
        assert response.url == reverse(
            "dashboard:offer-detail", kwargs={"pk": offer.pk}
        )
        assert [(m.level_tag, str(m.message)) for m in get_messages(request)][0] == (
            "warning",
            "This offer can only be deleted if it has no vouchers attached to it",
        )
        assert ConditionalOffer.objects.exists()

    def test_range_product_list_view(self, rf, range_with_products):
        view = range_views.RangeProductListView.as_view()
        pk = range_with_products.pk

        request = rf.get("/")
        response = view(request, pk=pk)
        # if these are missing the pagination is broken
        assert response.context_data["paginator"]
        assert response.context_data["page_obj"]
        assert response.status_code == 200


class TestCreateOfferWizardStepView(TestCase):
    def setUp(self):
        range_ = RangeFactory()

        self.metadata_form_kwargs_session_data = {
            "data": {
                "name": "Test offer",
                "slug": "",
                "description": "Test description",
                "offer_type": ConditionalOffer.SITE,
                "exclusive": True,
                "status": ConditionalOffer.OPEN,
                "condition": None,
                "benefit": None,
                "priority": 0,
                "start_datetime": None,
                "end_datetime": None,
                "max_global_applications": None,
                "max_user_applications": None,
                "max_basket_applications": None,
                "max_discount": None,
                "total_discount": "0.00",
                "num_applications": 0,
                "num_orders": 0,
                "redirect_url": "",
                "date_created": None,
            },
        }
        self.metadata_obj_session_data = [
            {
                "model": "offer.conditionaloffer",
                "pk": None,
                "fields": {
                    "name": "Test offer",
                    "description": "Test description",
                    "offer_type": ConditionalOffer.SITE,
                },
            }
        ]
        self.benefit_form_kwargs_session_data = {
            "data": {
                "range": range_.pk,
                "type": Benefit.PERCENTAGE,
                "value": "10",
                "max_affected_items": None,
                "custom_benefit": "",
            },
        }
        self.benefit_obj_session_data = [
            {
                "model": "offer.benefit",
                "pk": None,
                "fields": {
                    "range": range_.pk,
                    "type": Benefit.PERCENTAGE,
                    "value": "10",
                    "max_affected_items": None,
                    "proxy_class": None,
                },
            }
        ]
        self.condition_form_kwargs_session_data = {
            "data": {
                "range": range_.pk,
                "type": Condition.COUNT,
                "value": "10",
                "custom_condition": "",
            },
        }
        self.condition_obj_session_data = [
            {
                "model": "offer.condition",
                "pk": None,
                "fields": {
                    "range": range_.pk,
                    "type": Condition.COUNT,
                    "value": "10",
                    "proxy_class": None,
                },
            }
        ]

    def test_offer_meta_data_view(self):
        request = RequestFactory().post(
            "/",
            data={
                "name": "Test offer",
                "description": "Test description",
                "offer_type": ConditionalOffer.SITE,
            },
        )
        response = offer_views.OfferMetaDataView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:offer-benefit"))
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata"],
            {
                "data": {
                    "name": "Test offer",
                    "description": "Test description",
                    "offer_type": ConditionalOffer.SITE,
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata_obj"],
            [
                {
                    "model": "offer.conditionaloffer",
                    "pk": None,
                    "fields": {
                        "name": "Test offer",
                        "slug": "",
                        "description": "Test description",
                        "offer_type": ConditionalOffer.SITE,
                        "exclusive": True,
                        "status": ConditionalOffer.OPEN,
                        "condition": None,
                        "benefit": None,
                        "priority": 0,
                        "start_datetime": None,
                        "end_datetime": None,
                        "max_global_applications": None,
                        "max_user_applications": None,
                        "max_basket_applications": None,
                        "max_discount": None,
                        "total_discount": "0.00",
                        "num_applications": 0,
                        "num_orders": 0,
                        "redirect_url": "",
                        "date_created": None,
                    },
                }
            ],
        )

    def test_offer_benefit_view_with_built_in_benefit_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post(
            "/",
            data={
                "range": range_.pk,
                "type": Benefit.PERCENTAGE,
                "value": 10,
            },
        )
        request.session["offer_wizard"] = {
            "metadata": json.dumps(self.metadata_form_kwargs_session_data),
            "metadata_obj": json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:offer-condition"))
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata"],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata_obj"],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit"],
            {
                "data": {
                    "range": range_.pk,
                    "type": Benefit.PERCENTAGE,
                    "value": "10",
                    "max_affected_items": None,
                    "custom_benefit": "",
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit_obj"],
            [
                {
                    "model": "offer.benefit",
                    "pk": None,
                    "fields": {
                        "range": range_.pk,
                        "type": Benefit.PERCENTAGE,
                        "value": "10",
                        "max_affected_items": None,
                        "proxy_class": None,
                    },
                }
            ],
        )

    def test_offer_benefit_view_with_custom_benefit_type(self):
        benefit = create_benefit(CustomBenefitModel)

        request = RequestFactory().post(
            "/",
            data={
                "custom_benefit": benefit.pk,
            },
        )
        request.session["offer_wizard"] = {
            "metadata": json.dumps(self.metadata_form_kwargs_session_data),
            "metadata_obj": json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:offer-condition"))
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata"],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata_obj"],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit"],
            {
                "data": {
                    "range": None,
                    "type": "",
                    "value": None,
                    "max_affected_items": None,
                    "custom_benefit": str(benefit.pk),
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit_obj"],
            [
                {
                    "model": "offer.benefit",
                    "pk": benefit.pk,
                    "fields": {
                        "range": None,
                        "type": "",
                        "value": None,
                        "max_affected_items": None,
                        "proxy_class": benefit.proxy_class,
                    },
                }
            ],
        )

    def test_offer_condition_view_with_built_in_condition_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post(
            "/",
            data={
                "range": range_.pk,
                "type": Condition.COUNT,
                "value": 10,
            },
        )
        request.session["offer_wizard"] = {
            "metadata": json.dumps(self.metadata_form_kwargs_session_data),
            "metadata_obj": json.dumps(self.metadata_obj_session_data),
            "benefit": json.dumps(self.benefit_form_kwargs_session_data),
            "benefit_obj": json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:offer-restrictions"))
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata"],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata_obj"],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit"],
            self.benefit_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit_obj"],
            self.benefit_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["condition"],
            {
                "data": {
                    "range": range_.pk,
                    "type": Condition.COUNT,
                    "value": "10",
                    "custom_condition": "",
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["condition_obj"],
            [
                {
                    "model": "offer.condition",
                    "pk": None,
                    "fields": {
                        "range": range_.pk,
                        "type": Condition.COUNT,
                        "value": "10",
                        "proxy_class": None,
                    },
                }
            ],
        )

    def test_offer_condition_view_with_custom_condition_type(self):
        condition = create_condition(CustomConditionModel)

        request = RequestFactory().post(
            "/",
            data={
                "custom_condition": condition.pk,
            },
        )
        request.session["offer_wizard"] = {
            "metadata": json.dumps(self.metadata_form_kwargs_session_data),
            "metadata_obj": json.dumps(self.metadata_obj_session_data),
            "benefit": json.dumps(self.benefit_form_kwargs_session_data),
            "benefit_obj": json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:offer-restrictions"))
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata"],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["metadata_obj"],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit"],
            self.benefit_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["benefit_obj"],
            self.benefit_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["condition"],
            {
                "data": {
                    "range": None,
                    "type": "",
                    "value": None,
                    "custom_condition": str(condition.pk),
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"]["condition_obj"],
            [
                {
                    "model": "offer.condition",
                    "pk": condition.pk,
                    "fields": {
                        "range": None,
                        "type": "",
                        "value": None,
                        "proxy_class": condition.proxy_class,
                    },
                }
            ],
        )

    def test_offer_restrictions_view(self):
        request = RequestFactory().post(
            "/",
            data={
                "priority": 0,
            },
        )
        request.session["offer_wizard"] = {
            "metadata": json.dumps(self.metadata_form_kwargs_session_data),
            "metadata_obj": json.dumps(self.metadata_obj_session_data),
            "benefit": json.dumps(self.benefit_form_kwargs_session_data),
            "benefit_obj": json.dumps(self.benefit_obj_session_data),
            "condition": json.dumps(self.condition_form_kwargs_session_data),
            "condition_obj": json.dumps(self.condition_obj_session_data),
        }
        response = offer_views.OfferRestrictionsView.as_view()(request)

        offer = ConditionalOffer.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("dashboard:offer-detail", kwargs={"pk": offer.pk})
        )
        self.assertEqual(
            [(m.level_tag, str(m.message)) for m in get_messages(request)][0],
            ("success", "Offer '%s' created!" % offer.name),
        )
        self.assertEqual(request.session["offer_wizard"], {})


@freeze_time("2021-04-23 14:00:00")
class TestUpdateOfferWizardStepView(TestCase):
    def setUp(self):
        self.offer = ConditionalOfferFactory()
        self.metadata_form_kwargs_key = "metadata%s" % self.offer.pk
        self.metadata_obj_key = "metadata%s_obj" % self.offer.pk
        self.benefit_form_kwargs_key = "benefit%s" % self.offer.pk
        self.benefit_obj_key = "benefit%s_obj" % self.offer.pk
        self.condition_form_kwargs_key = "condition%s" % self.offer.pk
        self.condition_obj_key = "condition%s_obj" % self.offer.pk
        range_ = RangeFactory()

        self.metadata_form_kwargs_session_data = {
            "data": {
                "name": "Test offer",
                "slug": self.offer.slug,
                "description": "Test description",
                "offer_type": ConditionalOffer.VOUCHER,
                "exclusive": True,
                "status": ConditionalOffer.OPEN,
                "condition": self.offer.condition.pk,
                "benefit": self.offer.benefit.pk,
                "priority": 0,
                "start_datetime": None,
                "end_datetime": None,
                "max_global_applications": None,
                "max_user_applications": None,
                "max_basket_applications": None,
                "max_discount": None,
                "total_discount": "0.00",
                "num_applications": 0,
                "num_orders": 0,
                "redirect_url": "",
                "date_created": "2021-04-23T14:00:00Z",
            },
        }
        self.metadata_obj_session_data = [
            {
                "model": "offer.conditionaloffer",
                "pk": None,
                "fields": {
                    "name": "Test offer",
                    "description": "Test description",
                    "offer_type": ConditionalOffer.VOUCHER,
                },
            }
        ]
        self.benefit_form_kwargs_session_data = {
            "data": {
                "range": range_.pk,
                "type": Benefit.FIXED,
                "value": "2000",
                "max_affected_items": 2,
                "custom_benefit": "",
            },
        }
        self.benefit_obj_session_data = [
            {
                "model": "offer.benefit",
                "pk": None,
                "fields": {
                    "range": range_.pk,
                    "type": Benefit.FIXED,
                    "value": "2000",
                    "max_affected_items": 2,
                    "proxy_class": "",
                },
            }
        ]
        self.condition_form_kwargs_session_data = {
            "data": {
                "range": range_.pk,
                "type": Condition.VALUE,
                "value": "2000",
                "custom_condition": "",
            },
        }
        self.condition_obj_session_data = [
            {
                "model": "offer.condition",
                "pk": None,
                "fields": {
                    "range": range_.pk,
                    "type": Condition.VALUE,
                    "value": "2000",
                    "proxy_class": "",
                },
            }
        ]

    def test_offer_meta_data_view(self):
        request = RequestFactory().post(
            "/",
            data={
                "name": "Test offer",
                "description": "Test description",
                "offer_type": ConditionalOffer.VOUCHER,
            },
        )
        response = offer_views.OfferMetaDataView.as_view(update=True)(
            request, pk=self.offer.pk
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard:offer-benefit", kwargs={"pk": self.offer.pk}),
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_form_kwargs_key],
            {
                "data": {
                    "name": "Test offer",
                    "description": "Test description",
                    "offer_type": ConditionalOffer.VOUCHER,
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_obj_key],
            [
                {
                    "model": "offer.conditionaloffer",
                    "pk": self.offer.pk,
                    "fields": {
                        "name": "Test offer",
                        "slug": self.offer.slug,
                        "description": "Test description",
                        "offer_type": ConditionalOffer.VOUCHER,
                        "exclusive": True,
                        "status": ConditionalOffer.OPEN,
                        "condition": self.offer.condition.pk,
                        "benefit": self.offer.benefit.pk,
                        "priority": 0,
                        "start_datetime": None,
                        "end_datetime": None,
                        "max_global_applications": None,
                        "max_user_applications": None,
                        "max_basket_applications": None,
                        "max_discount": None,
                        "total_discount": "0.00",
                        "num_applications": 0,
                        "num_orders": 0,
                        "redirect_url": "",
                        "date_created": "2021-04-23T14:00:00Z",
                    },
                }
            ],
        )

    def test_offer_benefit_view_with_built_in_benefit_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post(
            "/",
            data={
                "range": range_.pk,
                "type": Benefit.FIXED,
                "value": 2000,
            },
        )
        request.session["offer_wizard"] = {
            self.metadata_form_kwargs_key: json.dumps(
                self.metadata_form_kwargs_session_data
            ),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view(update=True)(
            request, pk=self.offer.pk
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard:offer-condition", kwargs={"pk": self.offer.pk}),
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_form_kwargs_key],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_obj_key],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_form_kwargs_key],
            {
                "data": {
                    "range": range_.pk,
                    "type": Benefit.FIXED,
                    "value": "2000",
                    "max_affected_items": None,
                    "custom_benefit": "",
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_obj_key],
            [
                {
                    "model": "offer.benefit",
                    "pk": self.offer.benefit.pk,
                    "fields": {
                        "range": range_.pk,
                        "type": Benefit.FIXED,
                        "value": "2000",
                        "max_affected_items": None,
                        "proxy_class": "",
                    },
                }
            ],
        )

    def test_offer_benefit_view_with_custom_benefit_type(self):
        benefit = create_benefit(CustomBenefitModel)

        request = RequestFactory().post(
            "/",
            data={
                "custom_benefit": benefit.pk,
            },
        )
        request.session["offer_wizard"] = {
            self.metadata_form_kwargs_key: json.dumps(
                self.metadata_form_kwargs_session_data
            ),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
        }
        response = offer_views.OfferBenefitView.as_view(update=True)(
            request, pk=self.offer.pk
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard:offer-condition", kwargs={"pk": self.offer.pk}),
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_form_kwargs_key],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_obj_key],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_form_kwargs_key],
            {
                "data": {
                    "range": None,
                    "type": "",
                    "value": None,
                    "max_affected_items": None,
                    "custom_benefit": str(benefit.pk),
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_obj_key],
            [
                {
                    "model": "offer.benefit",
                    "pk": benefit.pk,
                    "fields": {
                        "range": None,
                        "type": "",
                        "value": None,
                        "max_affected_items": None,
                        "proxy_class": benefit.proxy_class,
                    },
                }
            ],
        )

    def test_offer_condition_view_with_built_in_condition_type(self):
        range_ = RangeFactory()

        request = RequestFactory().post(
            "/",
            data={
                "range": range_.pk,
                "type": Condition.VALUE,
                "value": 2000,
            },
        )
        request.session["offer_wizard"] = {
            self.metadata_form_kwargs_key: json.dumps(
                self.metadata_form_kwargs_session_data
            ),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
            self.benefit_form_kwargs_key: json.dumps(
                self.benefit_form_kwargs_session_data
            ),
            self.benefit_obj_key: json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view(update=True)(
            request, pk=self.offer.pk
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard:offer-restrictions", kwargs={"pk": self.offer.pk}),
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_form_kwargs_key],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_obj_key],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_form_kwargs_key],
            self.benefit_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_obj_key],
            self.benefit_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.condition_form_kwargs_key],
            {
                "data": {
                    "range": range_.pk,
                    "type": Condition.VALUE,
                    "value": "2000",
                    "custom_condition": "",
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.condition_obj_key],
            [
                {
                    "model": "offer.condition",
                    "pk": self.offer.condition.pk,
                    "fields": {
                        "range": range_.pk,
                        "type": Condition.VALUE,
                        "value": "2000",
                        "proxy_class": "",
                    },
                }
            ],
        )

    def test_offer_condition_view_with_custom_condition_type(self):
        condition = create_condition(CustomConditionModel)

        request = RequestFactory().post(
            "/",
            data={
                "custom_condition": condition.pk,
            },
        )
        request.session["offer_wizard"] = {
            self.metadata_form_kwargs_key: json.dumps(
                self.metadata_form_kwargs_session_data
            ),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
            self.benefit_form_kwargs_key: json.dumps(
                self.benefit_form_kwargs_session_data
            ),
            self.benefit_obj_key: json.dumps(self.benefit_obj_session_data),
        }
        response = offer_views.OfferConditionView.as_view(update=True)(
            request, pk=self.offer.pk
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard:offer-restrictions", kwargs={"pk": self.offer.pk}),
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_form_kwargs_key],
            self.metadata_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.metadata_obj_key],
            self.metadata_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_form_kwargs_key],
            self.benefit_form_kwargs_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.benefit_obj_key],
            self.benefit_obj_session_data,
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.condition_form_kwargs_key],
            {
                "data": {
                    "range": None,
                    "type": "",
                    "value": None,
                    "custom_condition": str(condition.pk),
                },
            },
        )
        self.assertJSONEqual(
            request.session["offer_wizard"][self.condition_obj_key],
            [
                {
                    "model": "offer.condition",
                    "pk": condition.pk,
                    "fields": {
                        "range": None,
                        "type": "",
                        "value": None,
                        "proxy_class": condition.proxy_class,
                    },
                }
            ],
        )

    def test_offer_restrictions_view(self):
        request = RequestFactory().post(
            "/",
            data={
                "priority": 0,
            },
        )
        request.session["offer_wizard"] = {
            self.metadata_form_kwargs_key: json.dumps(
                self.metadata_form_kwargs_session_data
            ),
            self.metadata_obj_key: json.dumps(self.metadata_obj_session_data),
            self.benefit_form_kwargs_key: json.dumps(
                self.benefit_form_kwargs_session_data
            ),
            self.benefit_obj_key: json.dumps(self.benefit_obj_session_data),
            self.condition_form_kwargs_key: json.dumps(
                self.condition_form_kwargs_session_data
            ),
            self.condition_obj_key: json.dumps(self.condition_obj_session_data),
        }
        response = offer_views.OfferRestrictionsView.as_view(update=True)(
            request, pk=self.offer.pk
        )

        self.offer.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard:offer-detail", kwargs={"pk": self.offer.pk}),
        )
        self.assertEqual(
            [(m.level_tag, str(m.message)) for m in get_messages(request)][0],
            ("success", "Offer '%s' updated" % self.offer.name),
        )
        self.assertEqual(request.session["offer_wizard"], {})
