from oscar.core.loading import is_model_registered
from oscar.apps.shipping import abstract_models


if not is_model_registered('shipping', 'OrderAndItemCharges'):
    class OrderAndItemCharges(abstract_models.AbstractOrderAndItemCharges):
        pass


if not is_model_registered('shipping', 'WeightBased'):
    class WeightBased(abstract_models.AbstractWeightBased):
        pass


if not is_model_registered('shipping', 'WeightBand'):
    class WeightBand(abstract_models.AbstractWeightBand):
        pass
