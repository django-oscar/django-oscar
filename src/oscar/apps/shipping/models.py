from oscar.core.loading import is_model_registered
from oscar.apps.shipping import abstract_models

__all__ = []


if not is_model_registered('shipping', 'OrderAndItemCharges'):
    class OrderAndItemCharges(abstract_models.AbstractOrderAndItemCharges):
        pass

    __all__.append('OrderAndItemCharges')
