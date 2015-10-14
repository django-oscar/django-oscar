from oscar.apps.shipping import abstract_models
from oscar.core.loading import is_model_registered

__all__ = []


if not is_model_registered('shipping', 'OrderAndItemCharges'):
    class OrderAndItemCharges(abstract_models.AbstractOrderAndItemCharges):
        pass

    __all__.append('OrderAndItemCharges')


if not is_model_registered('shipping', 'WeightBased'):
    class WeightBased(abstract_models.AbstractWeightBased):
        pass

    __all__.append('WeightBased')


if not is_model_registered('shipping', 'WeightBand'):
    class WeightBand(abstract_models.AbstractWeightBand):
        pass

    __all__.append('WeightBand')
