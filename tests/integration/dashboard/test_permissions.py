from django.urls import reverse

from oscar.core.compat import get_user_model
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
User = get_user_model()


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
            "permissions": DashboardPermission.get("offer", "view_conditionaloffer"),
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
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "add_product"
                ),
            },
            {
                "name": "dashboard:catalogue-product-create",
                "kwargs": {"product_class_slug": product_class.slug},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "add_product"
                ),
            },
            {
                "name": "dashboard:catalogue-product-create-child",
                "kwargs": {"parent_pk": parent_product.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "add_product"
                ),
            },
            {
                "name": "dashboard:catalogue-category-create",
                "permissions": DashboardPermission.get(
                    "catalogue", "view_category", "add_category"
                ),
            },
            {
                "name": "dashboard:catalogue-category-create-child",
                "kwargs": {"parent": category.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_category", "add_category"
                ),
            },
            {
                "name": "dashboard:catalogue-class-create",
                "permissions": DashboardPermission.get(
                    "catalogue", "view_productclass", "add_productclass"
                ),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-create",
                "permissions": DashboardPermission.get(
                    "catalogue", "view_attributeoptiongroup", "add_attributeoptiongroup"
                ),
            },
            {
                "name": "dashboard:catalogue-option-create",
                "permissions": DashboardPermission.get(
                    "catalogue", "view_option", "add_option"
                ),
            },
            # Update Views
            {
                "name": "dashboard:catalogue-category-update",
                "kwargs": {"pk": category.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_category", "change_category"
                ),
            },
            {
                "name": "dashboard:catalogue-class-update",
                "kwargs": {"pk": product_class.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "change_productclass", "view_productclass"
                ),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-update",
                "kwargs": {"pk": attribute_option_group.id},
                "permissions": DashboardPermission.get(
                    "catalogue",
                    "view_attributeoptiongroup",
                    "change_attributeoptiongroup",
                ),
            },
            {
                "name": "dashboard:catalogue-option-update",
                "kwargs": {"pk": option.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_option", "change_option"
                ),
            },
            # List Views
            {
                "name": "dashboard:catalogue-product-list",
                "permissions": DashboardPermission.get("catalogue", "view_product"),
            },
            {
                "name": "dashboard:stock-alert-list",
                "permissions": DashboardPermission.get("partner", "view_stockalert"),
            },
            {
                "name": "dashboard:catalogue-category-list",
                "permissions": DashboardPermission.get("catalogue", "view_category"),
            },
            {
                "name": "dashboard:catalogue-class-list",
                "permissions": DashboardPermission.get(
                    "catalogue", "view_productclass"
                ),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-list",
                "permissions": DashboardPermission.get(
                    "catalogue", "view_attributeoptiongroup"
                ),
            },
            {
                "name": "dashboard:catalogue-option-list",
                "permissions": DashboardPermission.get("catalogue", "view_option"),
            },
            # Detail Views
            {
                "name": "dashboard:catalogue-product",
                "kwargs": {"pk": product.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "add_product", "change_product"
                ),
            },
            {
                "name": "dashboard:catalogue-product-lookup",
                "permissions": DashboardPermission.get("catalogue", "view_product"),
            },
            {
                "name": "dashboard:catalogue-category-detail-list",
                "kwargs": {"pk": category.id},
                "permissions": DashboardPermission.get("catalogue", "view_category"),
            },
            # Delete Views
            {
                "name": "dashboard:catalogue-product-delete",
                "kwargs": {"pk": product.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "delete_product"
                ),
            },
            {
                "name": "dashboard:catalogue-category-delete",
                "kwargs": {"pk": category.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_category", "delete_category"
                ),
            },
            {
                "name": "dashboard:catalogue-class-delete",
                "kwargs": {"pk": product_class.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_productclass", "delete_productclass"
                ),
            },
            {
                "name": "dashboard:catalogue-attribute-option-group-delete",
                "kwargs": {"pk": attribute_option_group.id},
                "permissions": DashboardPermission.get(
                    "catalogue",
                    "view_attributeoptiongroup",
                    "delete_attributeoptiongroup",
                ),
            },
            {
                "name": "dashboard:catalogue-option-delete",
                "kwargs": {"pk": option.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_option", "delete_option"
                ),
            },
            # Test partner access to catalogue product views
            # Create Views
            {
                "name": "dashboard:catalogue-product-create",
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "add_product"
                ),
            },
            {
                "name": "dashboard:catalogue-product-create",
                "kwargs": {"product_class_slug": product_class.slug},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "add_product"
                ),
            },
            # Detail Views
            {
                "name": "dashboard:catalogue-product",
                "kwargs": {"pk": product.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "add_product", "change_product"
                ),
            },
            {
                "name": "dashboard:catalogue-product-lookup",
                "permissions": DashboardPermission.get("catalogue", "view_product"),
            },
            # List Views
            {
                "name": "dashboard:catalogue-product-list",
                "permissions": DashboardPermission.get("catalogue", "view_product"),
            },
            # Delete Views
            {
                "name": "dashboard:catalogue-product-delete",
                "kwargs": {"pk": product.id},
                "permissions": DashboardPermission.get(
                    "catalogue", "view_product", "delete_product"
                ),
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
                "permissions": DashboardPermission.get(
                    "communication", "view_communicationeventtype"
                ),
            },
            {
                "name": "dashboard:comms-update",
                "kwargs": {"slug": communication_event_type.code},
                "permissions": DashboardPermission.get(
                    "communication",
                    "change_communicationeventtype",
                    "view_communicationeventtype",
                ),
            },
        ]


class OfferDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        offer = ConditionalOfferFactory()

        create_update_perm = DashboardPermission.get(
            "offer",
            "add_conditionaloffer",
            "change_conditionaloffer",
            "view_conditionaloffer",
        )

        return [
            # List and Detail Views
            {
                "name": "dashboard:offer-list",
                "permissions": DashboardPermission.get(
                    "offer", "view_conditionaloffer"
                ),
            },
            {
                "name": "dashboard:offer-detail",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get(
                    "offer", "view_conditionaloffer"
                ),
            },
            # Create + Update Views
            {
                "name": "dashboard:offer-metadata",
                "permissions": create_update_perm,
                "kwargs": {"pk": offer.id},
            },
            {
                "name": "dashboard:offer-condition",
                "permissions": create_update_perm,
                "kwargs": {"pk": offer.id},
            },
            {
                "name": "dashboard:offer-benefit",
                "permissions": create_update_perm,
                "kwargs": {"pk": offer.id},
            },
            {
                "name": "dashboard:offer-restrictions",
                "permissions": create_update_perm,
                "kwargs": {"pk": offer.id},
            },
            # Delete Views
            {
                "name": "dashboard:offer-delete",
                "kwargs": {"pk": offer.id},
                "permissions": DashboardPermission.get(
                    "offer", "delete_conditionaloffer", "view_conditionaloffer"
                ),
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
                "permissions": DashboardPermission.get("order", "view_order"),
            },
            {
                "name": "dashboard:order-stats",
                "permissions": DashboardPermission.get("order", "view_order"),
            },
            {
                "name": "dashboard:order-detail",
                "kwargs": {"number": order.number},
                "permissions": DashboardPermission.get("order", "view_order"),
            },
            {
                "name": "dashboard:order-detail-note",
                "kwargs": {"number": order.number, "note_id": note.id},
                "permissions": DashboardPermission.get(
                    "order", "view_order", "change_order"
                ),
            },
            {
                "name": "dashboard:order-line-detail",
                "kwargs": {"number": order.number, "line_id": line.id},
                "permissions": DashboardPermission.get("order", "view_order"),
            },
            {
                "name": "dashboard:order-shipping-address",
                "kwargs": {"number": order.number},
                "permissions": DashboardPermission.get("order", "view_order"),
            },
            # Test that partner users can access the order
            {
                "name": "dashboard:order-list",
                "permissions": DashboardPermission.partner_dashboard_access,
            },
            {
                "name": "dashboard:order-stats",
                "permissions": DashboardPermission.partner_dashboard_access,
            },
            {
                "name": "dashboard:order-detail",
                "kwargs": {"number": order.number},
                "permissions": DashboardPermission.partner_dashboard_access,
            },
            {
                "name": "dashboard:order-detail-note",
                "kwargs": {"number": order.number, "note_id": note.id},
                "permissions": DashboardPermission.partner_dashboard_access,
            },
            {
                "name": "dashboard:order-line-detail",
                "kwargs": {"number": order.number, "line_id": line.id},
                "permissions": DashboardPermission.partner_dashboard_access,
            },
            {
                "name": "dashboard:order-shipping-address",
                "kwargs": {"number": order.number},
                "permissions": DashboardPermission.partner_dashboard_access,
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
                "permissions": DashboardPermission.get("flatpages", "view_flatpage"),
            },
            {
                "name": "dashboard:page-create",
                "permissions": DashboardPermission.get(
                    "flatpages", "view_flatpage", "add_flatpage"
                ),
            },
            {
                "name": "dashboard:page-update",
                "kwargs": {"pk": flatpage.id},
                "permissions": DashboardPermission.get(
                    "flatpages", "view_flatpage", "change_flatpage"
                ),
            },
            {
                "name": "dashboard:page-delete",
                "kwargs": {"pk": flatpage.id},
                "permissions": DashboardPermission.get(
                    "flatpages", "view_flatpage", "delete_flatpage"
                ),
            },
        ]


class PartnerDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        partner = PartnerFactory()
        partner.users.add(self.user)

        return [
            {
                "name": "dashboard:partner-list",
                "permissions": DashboardPermission.get("partner", "view_partner"),
            },
            {
                "name": "dashboard:partner-create",
                "permissions": DashboardPermission.get(
                    "partner", "view_partner", "add_partner"
                ),
            },
            {
                "name": "dashboard:partner-manage",
                "kwargs": {"pk": partner.id},
                "permissions": DashboardPermission.get("partner", "view_partner"),
            },
            {
                "name": "dashboard:partner-delete",
                "kwargs": {"pk": partner.id},
                "permissions": DashboardPermission.get(
                    "partner", "view_partner", "delete_partner"
                ),
            },
            {
                "name": "dashboard:partner-user-create",
                "kwargs": {"partner_pk": partner.id},
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user", "add_user"
                ),
            },
            {
                "name": "dashboard:partner-user-select",
                "kwargs": {"partner_pk": partner.id},
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user", "change_user"
                ),
            },
            {
                "name": "dashboard:partner-user-link",
                "kwargs": {"partner_pk": partner.id, "user_pk": self.user.id},
                "permissions": DashboardPermission.get("partner", "view_partner")
                + DashboardPermission.get(
                    User._meta.app_label, "view_user", "change_user"
                ),
            },
            {
                "name": "dashboard:partner-user-update",
                "kwargs": {"partner_pk": partner.id, "user_pk": self.user.id},
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user", "change_user"
                ),
            },
            {
                "name": "dashboard:partner-user-unlink",
                "kwargs": {"partner_pk": partner.id, "user_pk": self.user.id},
                "permissions": DashboardPermission.get("partner", "view_partner")
                + DashboardPermission.get(
                    User._meta.app_label, "view_user", "change_user"
                ),
                "method": "post",
            },
        ]


class RangeDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        offer_range = RangeFactory()

        return [
            {
                "name": "dashboard:range-list",
                "permissions": DashboardPermission.get("offer", "view_range"),
            },
            {
                "name": "dashboard:range-create",
                "permissions": DashboardPermission.get(
                    "offer", "view_range", "add_range"
                ),
            },
            {
                "name": "dashboard:range-update",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get(
                    "offer", "view_range", "change_range"
                ),
            },
            {
                "name": "dashboard:range-products",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get(
                    "offer", "view_range", "change_range"
                ),
            },
            {
                "name": "dashboard:range-reorder",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get(
                    "offer", "view_range", "change_range"
                ),
                "method": "post",
            },
            {
                "name": "dashboard:range-delete",
                "kwargs": {"pk": offer_range.id},
                "permissions": DashboardPermission.get(
                    "offer", "view_range", "delete_range"
                ),
            },
        ]


class ReportDashboardAccessTest(BaseViewPermissionTestCase):
    view_access_requirements = [
        {
            "name": "dashboard:reports-index",
            "permissions": DashboardPermission.get("analytics", "view_userrecord"),
        },
    ]


class ReviewDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        review = ProductReviewFactory()

        return [
            {
                "name": "dashboard:reviews-list",
                "permissions": DashboardPermission.get("reviews", "view_productreview"),
            },
            {
                "name": "dashboard:reviews-update",
                "kwargs": {"pk": review.id},
                "permissions": DashboardPermission.get(
                    "reviews", "change_productreview", "view_productreview"
                ),
            },
            {
                "name": "dashboard:reviews-delete",
                "kwargs": {"pk": review.id},
                "permissions": DashboardPermission.get(
                    "reviews", "delete_productreview", "view_productreview"
                ),
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
                "permissions": DashboardPermission.get("shipping", "view_weightbased"),
            },
            {
                "name": "dashboard:shipping-method-create",
                "permissions": DashboardPermission.get(
                    "shipping", "view_weightbased", "add_weightbased"
                ),
            },
            {
                "name": "dashboard:shipping-method-detail",
                "kwargs": {"pk": weight_based.id},
                "permissions": DashboardPermission.get("shipping", "view_weightbased"),
            },
            {
                "name": "dashboard:shipping-method-edit",
                "kwargs": {"pk": weight_based.id},
                "permissions": DashboardPermission.get(
                    "shipping", "change_weightbased", "view_weightbased"
                ),
            },
            {
                "name": "dashboard:shipping-method-delete",
                "kwargs": {"pk": weight_based.id},
                "permissions": DashboardPermission.get(
                    "shipping", "delete_weightbased", "view_weightbased"
                ),
            },
            {
                "name": "dashboard:shipping-method-band-edit",
                "kwargs": {"pk": weight_band.id, "method_pk": weight_based.id},
                "permissions": DashboardPermission.get(
                    "shipping", "change_weightbased", "view_weightbased"
                ),
            },
            {
                "name": "dashboard:shipping-method-band-delete",
                "kwargs": {"pk": weight_band.id, "method_pk": weight_based.id},
                "permissions": DashboardPermission.get(
                    "shipping", "delete_weightbased", "view_weightbased"
                ),
            },
        ]


class UserDashboardAccessTest(BaseViewPermissionTestCase):
    def get_view_access_requirements(self):
        alert = ProductAlertFactory()

        return [
            {
                "name": "dashboard:users-index",
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user"
                ),
            },
            {
                "name": "dashboard:user-detail",
                "kwargs": {"pk": self.user.id},
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user"
                ),
            },
            {
                "name": "dashboard:user-password-reset",
                "kwargs": {"pk": self.user.id},
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user", "change_user"
                ),
                "method": "post",
            },
            # Alerts
            {
                "name": "dashboard:user-alert-list",
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user"
                ),
            },
            {
                "name": "dashboard:user-alert-update",
                "kwargs": {"pk": alert.id},
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user", "change_user"
                ),
            },
            {
                "name": "dashboard:user-alert-delete",
                "kwargs": {"pk": alert.id},
                "permissions": DashboardPermission.get(
                    User._meta.app_label, "view_user", "delete_user"
                ),
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
                "permissions": DashboardPermission.get("voucher", "view_voucher"),
            },
            {
                "name": "dashboard:voucher-stats",
                "kwargs": {"pk": voucher.id},
                "permissions": DashboardPermission.get("voucher", "view_voucher"),
            },
            {
                "name": "dashboard:voucher-create",
                "permissions": DashboardPermission.get(
                    "voucher", "view_voucher", "add_voucher"
                ),
            },
            {
                "name": "dashboard:voucher-update",
                "kwargs": {"pk": voucher.id},
                "permissions": DashboardPermission.get(
                    "voucher", "view_voucher", "change_voucher"
                ),
            },
            {
                "name": "dashboard:voucher-delete",
                "kwargs": {"pk": voucher.id},
                "permissions": DashboardPermission.get(
                    "voucher", "view_voucher", "delete_voucher"
                ),
            },
            # Voucher Sets
            {
                "name": "dashboard:voucher-set-list",
                "permissions": DashboardPermission.get("voucher", "view_voucherset"),
            },
            {
                "name": "dashboard:voucher-set-create",
                "permissions": DashboardPermission.get(
                    "voucher", "view_voucherset", "add_voucherset"
                ),
            },
            {
                "name": "dashboard:voucher-set-update",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get(
                    "voucher", "view_voucherset", "change_voucherset"
                ),
            },
            {
                "name": "dashboard:voucher-set-detail",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get("voucher", "view_voucherset"),
            },
            {
                "name": "dashboard:voucher-set-download",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get("voucher", "view_voucherset"),
            },
            {
                "name": "dashboard:voucher-set-delete",
                "kwargs": {"pk": voucher_set.id},
                "permissions": DashboardPermission.get(
                    "voucher", "view_voucherset", "delete_voucherset"
                ),
            },
        ]
