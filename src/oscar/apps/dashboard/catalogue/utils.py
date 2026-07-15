from django.db.models import Q


def partner_product_visibility_q(user):
    """
    Q object matching products a stockrecord of one of the user's own
    partners actually belongs to — directly, or (for parent-structure
    products, which have no stockrecords of their own) via any child.
    """
    return Q(children__stockrecords__partner__users__pk=user.pk) | Q(
        stockrecords__partner__users__pk=user.pk
    )
