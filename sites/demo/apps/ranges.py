class AlphabetRange(object):
    name = "Products that start with D"

    def contains_product(self, product):
        return product.title.startswith('D')

    def num_products(self):
        return None