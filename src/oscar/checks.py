# pylint: disable=W0622
from django.core.checks import Error, Warning, register
from django.conf import settings
from django.db import connection


def turned_on_materialised_views():
    return (
        hasattr(settings, "OSCAR_CATALOGUE_USE_POSTGRES_MATERIALISED_VIEWS")
        and settings.OSCAR_CATALOGUE_USE_POSTGRES_MATERIALISED_VIEWS
    )


def is_postgres():
    return connection.vendor == "postgresql"


@register()
def startup_check(*args, **kwargs):
    errors = []

    if (
        hasattr(settings, "OSCAR_PRODUCT_SEARCH_HANDLER")
        and settings.OSCAR_PRODUCT_SEARCH_HANDLER is not None
    ):
        errors.append(
            Error(
                "The OSCAR_PRODUCT_SEARCH_HANDLER is removed since django-oscar==3.2.4.",
                hint="Use the new class based haystack views instead located in search.views. Any customizations that has been done to the search handler should be moved there.",
                id="django-oscar.E001",
            )
        )

    if turned_on_materialised_views() and not is_postgres():
        errors.append(
            Warning(
                "OSCAR_CATALOGUE_USE_POSTGRES_MATERIALISED_VIEWS is enabled but PostgreSQL is not detected. Materialized views are not functioning and fallback queries are being used instead.",
                hint="Either switch your database backend to PostgreSQL or disable the OSCAR_CATALOGUE_USE_POSTGRES_MATERIALISED_VIEWS setting in your configuration.",
                id="django-oscar.W001",
            )
        )
    return errors


def use_productcategory_materialised_view():
    return (
        is_postgres()
        and hasattr(settings, "OSCAR_CATALOGUE_USE_POSTGRES_MATERIALISED_VIEWS")
        and settings.OSCAR_CATALOGUE_USE_POSTGRES_MATERIALISED_VIEWS
    )
