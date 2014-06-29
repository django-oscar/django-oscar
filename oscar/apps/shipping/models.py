from django.conf import settings

from oscar.apps.shipping import abstract_models


if 'shipping.OrderAndItemCharges' not in settings.OSCAR_OVERRIDE_MODELS:
    class OrderAndItemCharges(abstract_models.AbstractOrderAndItemCharges):
        pass


if 'shipping.WeightBased' not in settings.OSCAR_OVERRIDE_MODELS:
    class WeightBased(abstract_models.AbstractWeightBased):
        pass


if 'shipping.WeightBand' not in settings.OSCAR_OVERRIDE_MODELS:
    class WeightBand(abstract_models.AbstractWeightBand):
        pass
