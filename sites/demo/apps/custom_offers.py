from oscar.apps.offer import models


class AlphabetRange(object):
    name = "Products that start with D"

    def contains_product(self, product):
        return product.title.startswith('D')

    def num_products(self):
        return None


class BasketOwnerCalledBarry(models.Condition):
    name = "User must be called barry"

    class Meta:
        proxy = True

    def is_satisfied(self, basket):
        if not basket.owner:
            return False
        return basket.owner.first_name.lower() == 'barry'

    def can_apply_condition(self, product):
        return False

    def consume_items(self, basket, affected_lines):
        return
