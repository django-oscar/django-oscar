from __future__ import unicode_literals

import django
from django.db import models


if django.VERSION >= (1, 10):
    SubfieldBase = type
else:
    SubfieldBase = models.SubfieldBase

if django.VERSION >= (1, 10):
    def get_fields_with_model(model_class):
        return [
            (f, f.model if f.model != model_class else None)
            for f in model_class._meta.get_fields()
            if not f.is_relation or f.one_to_one
            or (f.many_to_one and f.related_model)]
else:
    def get_fields_with_model(model_class):
        return model_class._meta.get_fields_with_model()
