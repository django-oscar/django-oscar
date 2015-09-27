import factory
from django.contrib.auth import models as auth_models

__all__ = ['PermissionFactory']


class PermissionFactory(factory.DjangoModelFactory):
    name = 'Dummy permission'
    codename = 'dummy'

    class Meta:
        model = auth_models.Permission
        django_get_or_create = ('content_type', 'codename')
