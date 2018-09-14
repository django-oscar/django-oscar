# -*- coding: utf-8 -*-
from oscar.core.loading import is_model_registered

from .abstract_models import *  # noqa

__all__ = []


if not is_model_registered('system', 'Configuration'):
    class Configuration(AbstractConfiguration):
        pass

    __all__.append('Configuration')
