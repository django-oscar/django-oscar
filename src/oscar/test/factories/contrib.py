import factory
from django.contrib.auth import models as auth_models
from django.contrib.sites import models as sites_models

__all__ = ["PermissionFactory", "SiteFactory"]


class PermissionFactory(factory.django.DjangoModelFactory):
    name = "Dummy permission"
    codename = "dummy"

    class Meta:
        model = auth_models.Permission
        django_get_or_create = ("content_type", "codename")


class SiteFactory(factory.django.DjangoModelFactory):
    domain = factory.Sequence(lambda n: "site-%d.oscarcommerce.com" % n)

    class Meta:
        model = sites_models.Site
        django_get_or_create = ("domain",)
