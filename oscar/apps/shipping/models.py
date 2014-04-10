from oscar.apps.shipping import abstract_models


# backwards-compatible import
ShippingMethod = abstract_models.ShippingMethod


class OrderAndItemCharges(abstract_models.AbstractOrderAndItemCharges):
    pass


class WeightBased(abstract_models.AbstractWeightBased):
    pass


class WeightBand(abstract_models.AbstractWeightBand):
    pass
