from oscar.core.loading import is_model_registered

from . import abstract_models

__all__ = []


if not is_model_registered("payment", "Transaction"):

    class Transaction(abstract_models.AbstractTransaction):
        pass

    __all__.append("Transaction")


if not is_model_registered("payment", "Source"):

    class Source(abstract_models.AbstractSource):
        pass

    __all__.append("Source")


if not is_model_registered("payment", "SourceType"):

    class SourceType(abstract_models.AbstractSourceType):
        pass

    __all__.append("SourceType")


if not is_model_registered("payment", "Bankcard"):

    class Bankcard(abstract_models.AbstractBankcard):
        pass

    __all__.append("Bankcard")
