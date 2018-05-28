from django.conf import settings
from django.db.models import SlugField as DjangoSlugField


class SlugField(DjangoSlugField):
    def __init__(self, *args, **kwargs):
        # not override parameter if it was passed explicitly,
        # so passed parameters takes precedence over the setting
        if settings.OSCAR_SLUG_ALLOW_UNICODE:
            kwargs.setdefault('allow_unicode', settings.OSCAR_SLUG_ALLOW_UNICODE)

        super().__init__(*args, **kwargs)
