"""
Regression tests for the Partner IDOR vulnerability fixed in issue #4580.

Before the fix, ProductCreateUpdateView.get_object() used an unfiltered
Product queryset when resolving parent_pk for child-product creation.  A
non-staff partner user could therefore pass any parent_pk and bypass the
partner-product access filter.

The fix changes:
    get_object_or_404(Product, pk=parent_pk)
to:
    get_object_or_404(self.get_queryset(), pk=parent_pk)

so the partner-filtered queryset is always used.
"""
from django.test import TestCase, RequestFactory

from oscar.core.loading import get_model
from oscar.test.factories import (
    PartnerFactory,
    UserFactory,
    create_product,
    create_stockrecord,
)
from oscar.apps.dashboard.catalogue.views import ProductCreateUpdateView

Product = get_model("catalogue", "Product")


def _make_request(user, method="get"):
    """Return a dummy request authenticated as *user*."""
    factory = RequestFactory()
    request = getattr(factory, method)("/")
    request.user = user
    return request


class TestProductCreateUpdateViewIDOR(TestCase):
    """
    Verify that get_queryset() is used when resolving parent_pk so that
    partner users cannot access parent products belonging to other partners.
    """

    def setUp(self):
        # Partner A owns product_a; partner_user belongs to partner A only.
        self.partner_a = PartnerFactory(name="Partner A")
        self.partner_user = UserFactory(is_staff=False)
        self.partner_a.users.add(self.partner_user)

        # Partner B owns product_b; partner_user has NO access to partner B.
        self.partner_b = PartnerFactory(name="Partner B")
        self.product_b = create_product(
            structure=Product.PARENT, title="B-Parent", partner_name=self.partner_b.name
        )
        create_stockrecord(self.product_b, partner_name=self.partner_b.name, price=10)

    def _make_view(self, user, parent_pk):
        """Instantiate a ProductCreateUpdateView as if the URL contained parent_pk."""
        request = _make_request(user)
        view = ProductCreateUpdateView()
        view.request = request
        view.kwargs = {"parent_pk": parent_pk}
        view.args = []
        return view

    def test_staff_user_can_access_any_parent_product(self):
        """Staff users bypass the partner filter and should always succeed."""
        staff = UserFactory(is_staff=True)
        view = self._make_view(staff, self.product_b.pk)
        # The queryset should include product_b for a staff user
        qs = view.get_queryset()
        self.assertIn(self.product_b, qs)

    def test_partner_user_cannot_access_other_partners_parent_product(self):
        """
        A non-staff partner user must NOT see a parent product that belongs
        exclusively to another partner.
        """
        view = self._make_view(self.partner_user, self.product_b.pk)
        qs = view.get_queryset()
        self.assertNotIn(
            self.product_b,
            qs,
            "Partner user should not have access to another partner's product",
        )

    def test_partner_user_can_access_own_parent_product(self):
        """A non-staff partner user must see products belonging to their partner."""
        product_a = create_product(
            structure=Product.PARENT,
            title="A-Parent",
            partner_name=self.partner_a.name,
            partner_users=[self.partner_user],
        )
        create_stockrecord(
            product_a,
            partner_name=self.partner_a.name,
            price=10,
            partner_users=[self.partner_user],
        )
        view = self._make_view(self.partner_user, product_a.pk)
        qs = view.get_queryset()
        self.assertIn(product_a, qs)
