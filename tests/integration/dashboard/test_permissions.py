from django.urls import reverse

from oscar.core.loading import get_model, get_class
from oscar.test.testcases import WebTestCase, add_permissions
from oscar.test.factories import (
    ProductFactory,
    ProductClassFactory,
    CategoryFactory,
    AttributeOptionGroupFactory,
    OptionFactory,
    ConditionalOfferFactory,
    OrderFactory,
    OrderLineFactory,
    PartnerFactory,
    RangeFactory,
    ProductReviewFactory,
    ProductAlertFactory,
    VoucherFactory,
    VoucherSetFactory,
)

FlatPage = get_model("flatpages", "FlatPage")
WeightBand = get_model("shipping", "WeightBand")
WeightBased = get_model("shipping", "WeightBased")
CommunicationEventType = get_model("communication", "CommunicationEventType")
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class BaseViewPermissionTestCase(WebTestCase):
    is_staff = True
    view_access_requirements = []

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def get_view_access_requirements(self):
        return self.view_access_requirements

    def test_view_access_restrictions(self):
        """
        This test verifies access permissions for a specified dashboard view by checking
        the following scenarios based on a provided view configuration:

        Example view configuration:
        view_access_requirements = [{
            "name": "dashboard:offer-list",
            "permissions": DashboardPermission.get("offer"),
        }]

        Test cases:
        1. Ensure that a staff user without the specified permissions is denied
           access to the view.
        2. Verify that when the specified permission is assigned to the staff user,
           they can successfully access the view.

        This ensures that access control for the dashboard views is working as expected.
        """
        for view in self.get_view_access_requirements():
            view_name = view["name"]
            method = getattr(self.client, view.get("method", "get"))

            with self.subTest(view=view_name):
                self.user.user_permissions.clear()
                url = reverse(view_name, kwargs=view.get("kwargs", {}))

                # Staff user without permissions should get 403 Forbidden
                response = method(url)
                self.assertNoAccess(
                    response,
                    f"Expected 403 for view {view_name} without permissions, "
                    f"got {response.status_code}",
                )

                # Assign permission to staff
                add_permissions(self.user, view["permissions"])

                # Staff user with permission should get 200 OK
                response = method(url, follow=True)
                self.assertIsOk(
                    response,
                    f"Expected 200 for view {view_name} with permissions, "
                    f"got {response.status_code}",
                )


class CatalogueDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        category = CategoryFactory()
        product_class = ProductClassFactory()
        parent_product = ProductFactory(structure="parent")
        product = ProductFactory()
        attribute_option_group = AttributeOptionGroupFactory()
        option = OptionFactory()

        return [
            # Create Views
            {
                "name": "dashboard:catalogue-product-create",
                "permissions": DashboardPermission.get("product"),
            },
            {
                "name": "dashboard:catalogue-product-create",
                "kwargs": {"product_class_slug": product_class.slug},
                "permissions": DashboardPermission.get("product"),
            },
            {
                "name": "dashboard:catalogue-product-create-child",
                "kwargs": {"parent_pk": parent_product.id},
                "permissions": DashboardPermission.get("product"),
            },
            {
                "name": "dashboard:catalogue-category-create",
                "permissions": DashboardPermission.get("category"),
            },
            {
                "name": "dashboard:catalogue-category-create-child",
                "kwargs": {"parent": category.id},
                "permissions": DashboardPermission.get("category"),
            },
            {
                "name": "dashboard:catalogue-class-create",
                "permissions": DashboardPermission.get("product_class"),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-create",
                "permissions": DashboardPermission.get("attribute_option_group"),
            },
            {
                "name": "dashboard:catalogue-option-create",
                "permissions": DashboardPermission.get("option"),
            },
            # Update Views
            {
                "name": "dashboard:catalogue-category-update",
                "kwargs": {"pk": category.id},
                "permissions": DashboardPermission.get("category"),
            },
            {
                "name": "dashboard:catalogue-class-update",
                "kwargs": {"pk": product_class.id},
                "permissions": DashboardPermission.get("product_class"),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-update",
                "kwargs": {"pk": attribute_option_group.id},
                "permissions": DashboardPermission.get("attribute_option_group"),
            },
            {
                "name": "dashboard:catalogue-option-update",
                "kwargs": {"pk": option.id},
                "permissions": DashboardPermission.get("option"),
            },
            # List Views
            {
                "name": "dashboard:catalogue-product-list",
                "permissions": DashboardPermission.get("product"),
            },
            {
                "name": "dashboard:stock-alert-list",
                "permissions": DashboardPermission.get("stockalert"),
            },
            {
                "name": "dashboard:catalogue-category-list",
                "permissions": DashboardPermission.get("category"),
            },
            {
                "name": "dashboard:catalogue-class-list",
                "permissions": DashboardPermission.get("product_class"),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-list",
                "permissions": DashboardPermission.get("attribute_option_group"),
            },
            {
                "name": "dashboard:catalogue-option-list",
                "permissions": DashboardPermission.get("option"),
            },
            # Detail Views
            {
                "name": "dashboard:catalogue-product",
                "kwargs": {"pk": product.id},
                "permissions": DashboardPermission.get("product"),
            },
            {
                "name": "dashboard:catalogue-product-lookup",
                "permissions": DashboardPermission.get("product"),
            },
            {
                "name": "dashboard:catalogue-category-detail-list",
                "kwargs": {"pk": category.id},
                "permissions": DashboardPermission.get("category"),
            },
            # Delete Views
            {
                "name": "dashboard:catalogue-product-delete",
                "kwargs": {"pk": product.id},
                "permissions": DashboardPermission.get("product"),
            },
            {
                "name": "dashboard:catalogue-category-delete",
                "kwargs": {"pk": category.id},
                "permissions": DashboardPermission.get("category"),
            },
            {
                "name": "dashboard:catalogue-class-delete",
                "kwargs": {"pk": product_class.id},
                "permissions": DashboardPermission.get("product_class"),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-delete",
                "kwargs": {"pk": attribute_option_group.id},
                "permissions": DashboardPermission.get("attribute_option_group"),
            },
            {
                "name": "dashboard:catalogue-option-delete",
                "kwargs": {"pk": option.id},
                "permissions": DashboardPermission.get("option"),
            },
        ]


class CommunicationDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        communication_event_type = CommunicationEventType.objects.create(
            name="comm-event",
            category=CommunicationEventType.USER_RELATED,
            code="Ûul-wįth-weird-chars",
        )

        return [
            {
                "name": "dashboard:comms-list",
                "permissions": DashboardPermission.get("communication_event_type"),
            },
            {
                "name": "dashboard:comms-update",
                "kwargs": {"slug": communication_event_type.code},
                "permissions": DashboardPermission.get("communication_event_type"),
            },
        ]


class OfferDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        offer = ConditionalOfferFactory()

        return [
            # List and Detail Views
            {
                "name": "dashboard:offer-list",
                "permissions": DashboardPermission.get("offer"),
            },
            {
                "name": "dashboard:offer-detail",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get("offer"),
            },
            # Create Views
            {
                "name": "dashboard:offer-metadata",
                "permissions": DashboardPermission.get("offer"),
            },
            {
                "name": "dashboard:offer-condition",
                "permissions": DashboardPermission.get("offer"),
            },
            {
                "name": "dashboard:offer-benefit",
                "permissions": DashboardPermission.get("offer"),
            },
            {
                "name": "dashboard:offer-restrictions",
                "permissions": DashboardPermission.get("offer"),
            },
            # Update Views
            {
                "name": "dashboard:offer-metadata",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get("offer"),
            },
            {
                "name": "dashboard:offer-condition",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get("offer"),
            },
            {
                "name": "dashboard:offer-benefit",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get("offer"),
            },
            {
                "name": "dashboard:offer-restrictions",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get("offer"),
            },
            # Delete Views
            {
                "name": "dashboard:offer-delete",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get("offer"),
            },
        ]


class OrderDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        order = OrderFactory()
        line = OrderLineFactory(order=order)
        note = order.notes.create(message="test")

        return [
            {
                "name": "dashboard:order-list",
                "permissions": DashboardPermission.get("order"),
            },
            {
                "name": "dashboard:order-stats",
                "permissions": DashboardPermission.get("order"),
            },
            {
                "name": "dashboard:order-detail",
                "kwargs": {"number": order.number},
                "permissions": DashboardPermission.get("order"),
            },
            {
                "name": "dashboard:order-detail-note",
                "kwargs": {"number": order.number, "note_id": note.id},
                "permissions": DashboardPermission.get("order"),
            },
            {
                "name": "dashboard:order-line-detail",
                "kwargs": {"number": order.number, "line_id": line.id},
                "permissions": DashboardPermission.get("order"),
            },
            {
                "name": "dashboard:order-shipping-address",
                "kwargs": {"number": order.number},
                "permissions": DashboardPermission.get("order"),
            },
        ]


class PageDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        flatpage = FlatPage.objects.create(
            title="title1", url="/url1/", content="some content"
        )
        return [
            {
                "name": "dashboard:page-list",
                "permissions": DashboardPermission.get("flat_page"),
            },
            {
                "name": "dashboard:page-create",
                "permissions": DashboardPermission.get("flat_page"),
            },
            {
                "name": "dashboard:page-update",
                "kwargs": {"pk": flatpage.id},
                "permissions": DashboardPermission.get("flat_page"),
            },
            {
                "name": "dashboard:page-delete",
                "kwargs": {"pk": flatpage.id},
                "permissions": DashboardPermission.get("flat_page"),
            },
        ]


class PartnerDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        partner = PartnerFactory()
        partner.users.add(self.user)

        return [
            {
                "name": "dashboard:partner-list",
                "permissions": DashboardPermission.get("partner"),
            },
            {
                "name": "dashboard:partner-create",
                "permissions": DashboardPermission.get("partner"),
            },
            {
                "name": "dashboard:partner-manage",
                "kwargs": {"pk": partner.id},
                "permissions": DashboardPermission.get("partner"),
            },
            {
                "name": "dashboard:partner-user-create",
                "kwargs": {"partner_pk": partner.id},
                "permissions": DashboardPermission.get("partner"),
            },
            {
                "name": "dashboard:partner-user-select",
                "kwargs": {"partner_pk": partner.id},
                "permissions": DashboardPermission.get("partner"),
            },
            {
                "name": "dashboard:partner-user-link",
                "kwargs": {"partner_pk": partner.id, "user_pk": self.user.id},
                "permissions": DashboardPermission.get("partner"),
            },
            {
                "name": "dashboard:partner-user-update",
                "kwargs": {"partner_pk": partner.id, "user_pk": self.user.id},
                "permissions": DashboardPermission.get("partner"),
            },
            {
                "name": "dashboard:partner-user-unlink",
                "kwargs": {"partner_pk": partner.id, "user_pk": self.user.id},
                "permissions": DashboardPermission.get("partner"),
                "method": "post",
            },
            {
                "name": "dashboard:partner-delete",
                "kwargs": {"pk": partner.id},
                "permissions": DashboardPermission.get("partner"),
            },
        ]


class RangeDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        offer_range = RangeFactory()

        return [
            {
                "name": "dashboard:range-list",
                "permissions": DashboardPermission.get("range"),
            },
            {
                "name": "dashboard:range-create",
                "permissions": DashboardPermission.get("range"),
            },
            {
                "name": "dashboard:range-update",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get("range"),
            },
            {
                "name": "dashboard:range-products",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get("range"),
            },
            {
                "name": "dashboard:range-reorder",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get("range"),
                "method": "post",
            },
            {
                "name": "dashboard:range-delete",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get("range"),
            },
        ]


class ReportDashboardAccessTest(BaseViewPermissionTestCase):
    view_access_requirements = [
        {
            "name": "dashboard:reports-index",
            "permissions": DashboardPermission.get("user_record"),
        },
    ]


class ReviewDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        review = ProductReviewFactory()

        return [
            {
                "name": "dashboard:reviews-list",
                "permissions": DashboardPermission.get("product_review"),
            },
            {
                "name": "dashboard:reviews-update",
                "kwargs": {"pk": review.id},
                "permissions": DashboardPermission.get("product_review"),
            },
            {
                "name": "dashboard:reviews-delete",
                "kwargs": {"pk": review.id},
                "permissions": DashboardPermission.get("product_review"),
            },
        ]


class ShippingDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        weight_based = WeightBased.objects.create()
        weight_band = WeightBand.objects.create(
            method=weight_based, upper_limit=1, charge=1
        )

        return [
            {
                "name": "dashboard:shipping-method-list",
                "permissions": DashboardPermission.get("shipping_method"),
            },
            {
                "name": "dashboard:shipping-method-create",
                "permissions": DashboardPermission.get("shipping_method"),
            },
            {
                "name": "dashboard:shipping-method-detail",
                "kwargs": {"pk": weight_based.id},
                "permissions": DashboardPermission.get("shipping_method"),
            },
            {
                "name": "dashboard:shipping-method-edit",
                "kwargs": {"pk": weight_based.id},
                "permissions": DashboardPermission.get("shipping_method"),
            },
            {
                "name": "dashboard:shipping-method-delete",
                "kwargs": {"pk": weight_based.id},
                "permissions": DashboardPermission.get("shipping_method"),
            },
            {
                "name": "dashboard:shipping-method-band-edit",
                "kwargs": {"pk": weight_band.id, "method_pk": weight_based.id},
                "permissions": DashboardPermission.get("shipping_method"),
            },
            {
                "name": "dashboard:shipping-method-band-delete",
                "kwargs": {"pk": weight_band.id, "method_pk": weight_based.id},
                "permissions": DashboardPermission.get("shipping_method"),
            },
        ]


class UserDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        alert = ProductAlertFactory()

        return [
            {
                "name": "dashboard:users-index",
                "permissions": DashboardPermission.get("user"),
            },
            {
                "name": "dashboard:user-detail",
                "kwargs": {"pk": self.user.id},
                "permissions": DashboardPermission.get("user"),
            },
            {
                "name": "dashboard:user-password-reset",
                "kwargs": {"pk": self.user.id},
                "permissions": DashboardPermission.get("user"),
                "method": "post",
            },
            # Alerts
            {
                "name": "dashboard:user-alert-list",
                "permissions": DashboardPermission.get("user"),
            },
            {
                "name": "dashboard:user-alert-update",
                "kwargs": {"pk": alert.id},
                "permissions": DashboardPermission.get("user"),
            },
            {
                "name": "dashboard:user-alert-delete",
                "kwargs": {"pk": alert.id},
                "permissions": DashboardPermission.get("user"),
            },
        ]


class VoucherDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        voucher = VoucherFactory()
        voucher_set = VoucherSetFactory()

        return [
            # Vouchers
            {
                "name": "dashboard:voucher-list",
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-stats",
                "kwargs": {"pk": voucher.id},
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-create",
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-update",
                "kwargs": {"pk": voucher.id},
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-delete",
                "kwargs": {"pk": voucher.id},
                "permissions": DashboardPermission.get("voucher"),
            },
            # Voucher Sets
            {
                "name": "dashboard:voucher-set-list",
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-set-create",
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-set-update",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-set-detail",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-set-download",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get("voucher"),
            },
            {
                "name": "dashboard:voucher-set-delete",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get("voucher"),
            },
        ]
