"""Permissions used for different dashboard views."""

from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardPermission:
    """Permissions used for different dashboard views."""

    permissions = {
        # Catalogue
        "product": [
            "is_staff",
            "catalogue.add_product",
            "catalogue.change_product",
            "catalogue.view_product",
            "catalogue.delete_product",
        ],
        "category": [
            "is_staff",
            "catalogue.add_category",
            "catalogue.change_category",
            "catalogue.view_category",
            "catalogue.delete_category",
        ],
        "product_class": [
            "is_staff",
            "catalogue.add_productclass",
            "catalogue.change_productclass",
            "catalogue.view_productclass",
            "catalogue.delete_productclass",
        ],
        "attribute_option_group": [
            "is_staff",
            "catalogue.add_attributeoptiongroup",
            "catalogue.change_attributeoptiongroup",
            "catalogue.view_attributeoptiongroup",
            "catalogue.delete_attributeoptiongroup",
        ],
        "option": [
            "is_staff",
            "catalogue.add_option",
            "catalogue.change_option",
            "catalogue.view_option",
            "catalogue.delete_option",
        ],
        # Communications
        "communication_event_type": [
            "is_staff",
            "communication.add_communicationeventtype",
            "communication.change_communicationeventtype",
            "communication.view_communicationeventtype",
            "communication.delete_communicationeventtype",
        ],
        # Partners
        "stockalert": [
            "is_staff",
            "partner.add_stockalert",
            "partner.change_stockalert",
            "partner.view_stockalert",
            "partner.delete_stockalert",
        ],
        "partner": [
            "is_staff",
            "partner.add_partner",
            "partner.change_partner",
            "partner.view_partner",
            "partner.delete_partner",
        ],
        # Offers
        "offer": [
            "is_staff",
            "offer.add_conditionaloffer",
            "offer.change_conditionaloffer",
            "offer.view_conditionaloffer",
            "offer.delete_conditionaloffer",
        ],
        # Orders
        "order": [
            "is_staff",
            "order.add_order",
            "order.change_order",
            "order.view_order",
            "order.delete_order",
        ],
        # Flat Pages
        "flat_page": [
            "is_staff",
            "flatpages.add_flatpage",
            "flatpages.change_flatpage",
            "flatpages.view_flatpage",
            "flatpages.delete_flatpage",
        ],
        # Ranges
        "range": [
            "is_staff",
            "offer.add_range",
            "offer.change_range",
            "offer.view_range",
            "offer.delete_range",
        ],
        # Analytics
        "user_record": [
            "is_staff",
            "analytics.add_userrecord",
            "analytics.change_userrecord",
            "analytics.view_userrecord",
            "analytics.delete_userrecord",
        ],
        # Reviews
        "product_review": [
            "is_staff",
            "reviews.add_productreview",
            "reviews.change_productreview",
            "reviews.view_productreview",
            "reviews.delete_productreview",
        ],
        # Shipping
        "shipping_method": [
            "is_staff",
            "shipping.add_weightbased",
            "shipping.change_weightbased",
            "shipping.delete_weightbased",
            "shipping.view_weightbased",
        ],
        # Users
        "user": [
            "is_staff",
            f"{User._meta.app_label}.add_user",
            f"{User._meta.app_label}.change_user",
            f"{User._meta.app_label}.view_user",
            f"{User._meta.app_label}.delete_user",
        ],
        # Vouchers
        "voucher": [
            "is_staff",
            "voucher.add_voucher",
            "voucher.change_voucher",
            "voucher.view_voucher",
            "voucher.delete_voucher",
        ],
    }
    # Staff
    staff = ["is_staff"]
    # Partner Access
    partner_dashboard_access = ["partner.dashboard_access"]

    @classmethod
    def get(cls, *args):
        """
        DashboardPermission.get("product", "category", "stockalert")

        :return: list of permission codes
        """
        permissions = set()
        for arg in args:
            permissions.update(cls.permissions[arg])
        permissions.remove("is_staff")
        return list(permissions)

    @classmethod
    def get_all_permissions(cls):
        """
        Retrieve set of unique permissions defined in this class.
        """
        return set(
            [
                permission
                for permissions in cls.permissions.values()
                for permission in permissions
            ]
        )

    @classmethod
    def has_dashboard_perms(cls, user):
        """
        Check if user has any of the dashboard permissions.
        """
        return len(cls.get_all_permissions() & user.get_all_permissions()) > 0
