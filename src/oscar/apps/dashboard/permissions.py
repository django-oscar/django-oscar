"""Permissions used for different dashboard views."""

from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardPermission:
    """Permissions used for different dashboard views."""

    permissions = {
        # Catalogue
        "view-product": ["catalogue.view_product"],
        "add-product": ["catalogue.add_product"],
        "change-product": ["catalogue.change_product"],
        "delete-product": ["catalogue.delete_product"],
        "view-category": ["catalogue.view_category"],
        "add-category": ["catalogue.add_category"],
        "change-category": ["catalogue.change_category"],
        "delete-category": ["catalogue.delete_category"],
        "view-productclass": ["catalogue.view_productclass"],
        "add-productclass": ["catalogue.add_productclass"],
        "change-productclass": ["catalogue.change_productclass"],
        "delete-productclass": ["catalogue.delete_productclass"],
        "view-attributeoptiongroup": ["catalogue.view_attributeoptiongroup"],
        "add-attributeoptiongroup": ["catalogue.add_attributeoptiongroup"],
        "change-attributeoptiongroup": ["catalogue.change_attributeoptiongroup"],
        "delete-attributeoptiongroup": ["catalogue.delete_attributeoptiongroup"],
        "view-option": ["catalogue.view_option"],
        "add-option": ["catalogue.add_option"],
        "change-option": ["catalogue.change_option"],
        "delete-option": ["catalogue.delete_option"],
        # Communications
        "view-communication_event_type": ["communication.view_communicationeventtype"],
        "add-communication_event_type": ["communication.add_communicationeventtype"],
        "change-communication_event_type": [
            "communication.change_communicationeventtype"
        ],
        "delete-communication_event_type": [
            "communication.delete_communicationeventtype"
        ],
        # Partners
        "view-stockalert": ["partner.view_stockalert"],
        "add-stockalert": ["partner.add_stockalert"],
        "change-stockalert": ["partner.change_stockalert"],
        "delete-stockalert": ["partner.delete_stockalert"],
        "view-partner": ["partner.view_partner"],
        "add-partner": ["partner.add_partner"],
        "change-partner": ["partner.change_partner"],
        "delete-partner": ["partner.delete_partner"],
        # Offers
        "view-offer": ["offer.view_conditionaloffer"],
        "add-offer": ["offer.add_conditionaloffer"],
        "change-offer": ["offer.change_conditionaloffer"],
        "delete-offer": ["offer.delete_conditionaloffer"],
        "view-range": ["offer.view_range"],
        "add-range": ["offer.add_range"],
        "change-range": ["offer.change_range"],
        "delete-range": ["offer.delete_range"],
        # Orders
        "view-order": ["order.view_order"],
        "add-order": ["order.add_order"],
        "change-order": ["order.change_order"],
        "delete-order": ["order.delete_order"],
        # Flat Pages
        "view-flatpage": ["flatpages.view_flatpage"],
        "add-flatpage": ["flatpages.add_flatpage"],
        "change-flatpage": ["flatpages.change_flatpage"],
        "delete-flatpage": ["flatpages.delete_flatpage"],
        # Analytics
        "view-user_record": ["analytics.view_userrecord"],
        "add-user_record": ["analytics.add_userrecord"],
        "change-user_record": ["analytics.change_userrecord"],
        "delete-user_record": ["analytics.delete_userrecord"],
        # Reviews
        "view-product_review": ["reviews.view_productreview"],
        "add-product_review": ["reviews.add_productreview"],
        "change-product_review": ["reviews.change_productreview"],
        "delete-product_review": ["reviews.delete_productreview"],
        # Shipping
        "view-shipping_method": ["shipping.view_weightbased"],
        "add-shipping_method": ["shipping.add_weightbased"],
        "change-shipping_method": ["shipping.change_weightbased"],
        "delete-shipping_method": ["shipping.delete_weightbased"],
        # Users
        "view-user": [f"{User._meta.app_label}.view_user"],
        "add-user": [f"{User._meta.app_label}.add_user"],
        "change-user": [f"{User._meta.app_label}.change_user"],
        "delete-user": [f"{User._meta.app_label}.delete_user"],
        # Vouchers
        "view-voucher": ["voucher.view_voucher"],
        "add-voucher": ["voucher.add_voucher"],
        "change-voucher": ["voucher.change_voucher"],
        "delete-voucher": ["voucher.delete_voucher"],
    }
    # Staff
    staff = ["is_staff"]
    # Partner Access
    partner_dashboard_access = ["partner.dashboard_access"]

    @classmethod
    def get(cls, *args):
        """
        Get combined permissions for given keys.
        Example: DashboardPermission.get("view-product", "view-category")

        :return: list of permission codes
        """
        permissions = set()
        for arg in args:
            permissions.update(cls.permissions[arg])
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
