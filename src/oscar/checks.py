from django.core.checks import Error, register
from django.conf import settings


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
    return errors
