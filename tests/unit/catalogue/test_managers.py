import pytest

from oscar.apps.catalogue.models import Product
from oscar.test.factories import ProductFactory


@pytest.mark.django_db
def test_public_queryset_method_filters():
    ProductFactory(is_public=True)
    ProductFactory(is_public=False)
    assert Product.objects.public().count() == 1
