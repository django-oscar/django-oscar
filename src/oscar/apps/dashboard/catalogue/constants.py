from django.utils.translation import gettext_lazy as _

PRODUCT_BULK_ACTIONS = {
    "make_public": _("Make public"),
    "make_non_public": _("Make non-public"),
    "make_children_public": _("Make children public"),
    "make_children_non_public": _("Make children non-public"),
    "set_children_price": _("Set children price"),
}
