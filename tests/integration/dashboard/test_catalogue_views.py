# pylint: disable=attribute-defined-outside-init
from django.test import TestCase

from oscar.apps.dashboard.catalogue.views import ProductListView
from oscar.core.loading import get_model
from oscar.test.factories import create_product
from oscar.test.utils import RequestFactory

Product = get_model("catalogue", "Product")


class ProductListViewTestCase(TestCase):
    def test_searching_child_product_by_title_returns_parent_product(self):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Parent", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Child",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        view = ProductListView(request=RequestFactory().get("/?title=Child"))
        assert list(view.get_queryset()) == [self.parent_product]

    def test_searching_child_product_by_title_returns_1_parent_product_if_title_is_partially_shared(
        self,
    ):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Shared", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Shared",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        create_product(
            structure=Product.CHILD,
            title="Shared1",
            parent=self.parent_product,
            upc="CHILD_UPC1",
        )
        view = ProductListView(request=RequestFactory().get("/?title=Shared"))
        assert list(view.get_queryset()) == [self.parent_product]

    def test_searching_child_product_by_upc_returns_parent_product(self):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Parent", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Child",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        view = ProductListView(request=RequestFactory().get("/?upc=CHILD_UPC"))
        assert list(view.get_queryset()) == [self.parent_product]

    def test_searching_child_product_by_upc_returns_1_parent_product_if_upc_is_partially_shared(
        self,
    ):
        self.parent_product = create_product(
            structure=Product.PARENT, title="Parent", upc="PARENT_UPC"
        )
        create_product(
            structure=Product.CHILD,
            title="Child",
            parent=self.parent_product,
            upc="CHILD_UPC",
        )
        create_product(
            structure=Product.CHILD,
            title="Child1",
            parent=self.parent_product,
            upc="CHILD_UPC1",
        )
        view = ProductListView(request=RequestFactory().get("/?upc=CHILD"))
        assert list(view.get_queryset()) == [self.parent_product]
