import pytest
from django.core.exceptions import ValidationError

from oscar.apps.catalogue import models


def test_product_attributes_can_contain_underscores():
    attr = models.ProductAttribute(name="A", code="a_b")
    attr.full_clean()


def test_product_attributes_cant_contain_hyphens():
    attr = models.ProductAttribute(name="A", code="a-b")
    with pytest.raises(ValidationError):
        attr.full_clean()


def test_product_attributes_cant_be_python_keywords():
    attr = models.ProductAttribute(name="A", code="import")
    with pytest.raises(ValidationError):
        attr.full_clean()
