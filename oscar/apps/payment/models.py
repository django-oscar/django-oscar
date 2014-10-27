from oscar.core.loading import is_model_registered

from . import abstract_models


if not is_model_registered('payment', 'Transaction'):
    class Transaction(abstract_models.AbstractTransaction):
        pass


if not is_model_registered('payment', 'Source'):
    class Source(abstract_models.AbstractSource):
        pass


if not is_model_registered('payment', 'SourceType'):
    class SourceType(abstract_models.AbstractSourceType):
        pass


if not is_model_registered('payment', 'Bankcard'):
    class Bankcard(abstract_models.AbstractBankcard):
        pass
