from oscar.core.loading import is_model_registered

from .abstract_models import AbstractSynonym

__all__ = []


if not is_model_registered('search', 'Synonym'):
    class Synonym(AbstractSynonym):
        pass

    __all__.append('Synonym')
