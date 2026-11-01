from oscar.apps.shipping import repository

from apps.shipping.methods import FlatRate


class Repository(repository.Repository):
    def get_available_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        # built per call: the charge comes from the settings
        return [FlatRate()]
