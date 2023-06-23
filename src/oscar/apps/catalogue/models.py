# pylint: disable=wildcard-import, unused-wildcard-import

"""
Vanilla product models
"""
from oscar.apps.catalogue.abstract_models import *
from oscar.core.loading import is_model_registered

__all__ = ["ProductAttributesContainer"]


if not is_model_registered("catalogue", "ProductClass"):

    class ProductClass(AbstractProductClass):
        pass

    __all__.append("ProductClass")


if not is_model_registered("catalogue", "Category"):

    class Category(AbstractCategory):
        pass

    __all__.append("Category")


if not is_model_registered("catalogue", "ProductCategory"):

    class ProductCategory(AbstractProductCategory):
        pass

    __all__.append("ProductCategory")


if not is_model_registered("catalogue", "Product"):

    class Product(AbstractProduct):
        pass

    __all__.append("Product")


if not is_model_registered("catalogue", "ProductRecommendation"):

    class ProductRecommendation(AbstractProductRecommendation):
        pass

    __all__.append("ProductRecommendation")


if not is_model_registered("catalogue", "ProductAttribute"):

    class ProductAttribute(AbstractProductAttribute):
        pass

    __all__.append("ProductAttribute")


if not is_model_registered("catalogue", "ProductAttributeValue"):

    class ProductAttributeValue(AbstractProductAttributeValue):
        pass

    __all__.append("ProductAttributeValue")


if not is_model_registered("catalogue", "AttributeOptionGroup"):

    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        pass

    __all__.append("AttributeOptionGroup")


if not is_model_registered("catalogue", "AttributeOption"):

    class AttributeOption(AbstractAttributeOption):
        pass

    __all__.append("AttributeOption")


if not is_model_registered("catalogue", "Option"):

    class Option(AbstractOption):
        pass

    __all__.append("Option")


if not is_model_registered("catalogue", "ProductImage"):

    class ProductImage(AbstractProductImage):
        pass

    __all__.append("ProductImage")
