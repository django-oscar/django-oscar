from decimal import Decimal as D

from django.core.exceptions import ObjectDoesNotExist


class Scale(object):
    """
    For calculating the weight of a product or basket
    """

    def __init__(self, attribute_code="weight", default_weight=None):
        self.attribute = attribute_code
        self.default_weight = default_weight

    def weigh_product(self, product):
        weight = None
        try:
            weight = (
                product.get_attribute_values().get(attribute__code=self.attribute).value
            )
        except ObjectDoesNotExist:
            pass

        if weight is None:
            if self.default_weight is None:
                raise ValueError(
                    "No attribute %s found for product %s" % (self.attribute, product)
                )
            weight = self.default_weight

        return D(weight) if weight is not None else D("0.0")

    def weigh_basket(self, basket):
        weight = D("0.0")
        for line in basket.all_lines():
            weight += self.weigh_product(line.product) * line.quantity
        return weight
