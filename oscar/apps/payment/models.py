from django.conf import settings

from . import abstract_models


if 'payment.Transaction' not in settings.OSCAR_OVERRIDE_MODELS:
    class Transaction(abstract_models.AbstractTransaction):
        pass


if 'payment.Source' not in settings.OSCAR_OVERRIDE_MODELS:
    class Source(abstract_models.AbstractSource):
        pass


if 'payment.SourceType' not in settings.OSCAR_OVERRIDE_MODELS:
    class SourceType(abstract_models.AbstractSourceType):
        pass


if 'payment.Bankcard' not in settings.OSCAR_OVERRIDE_MODELS:
    class Bankcard(abstract_models.AbstractBankcard):
        pass
