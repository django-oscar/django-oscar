from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string


class AbstractThumbnailer(object):
    def generate_thumbnail(self, source, **opts):
        raise NotImplementedError

    def delete_thumbnails(self, source):
        raise NotImplementedError


class SorlThumbnail(AbstractThumbnailer):

    def __init__(self):
        if not apps.is_installed('sorl.thumbnail'):
            raise ValueError('"sorl.thumbnail" is not listed in "INSTALLED_APPS".')

    def generate_thumbnail(self, source, **opts):
        from sorl.thumbnail import get_thumbnail
        # Sorl can accept only: "width x height", "width", "x height".
        # https://sorl-thumbnail.readthedocs.io/en/latest/template.html#geometry
        # So for example value '50x' must be converted to '50'.
        size = opts.pop('size')
        width, height = size.split('x')
        # Set `size` to `width` if `height` is not provided.
        size = size if height else width
        return get_thumbnail(source, size, **opts)

    def delete_thumbnails(self, source):
        from sorl.thumbnail import delete
        from sorl.thumbnail.helpers import ThumbnailError
        try:
            delete(source)
        except ThumbnailError:
            pass


class EasyThumbnails(AbstractThumbnailer):

    def __init__(self):
        if not apps.is_installed('easy_thumbnails'):
            raise ValueError('"easy_thumbnails" is not listed in "INSTALLED_APPS".')

    def generate_thumbnail(self, source, **opts):
        from easy_thumbnails.files import get_thumbnailer
        width, height = opts['size'].split('x')
        width = width or 0
        height = height or 0
        opts['size'] = (width, height)
        return get_thumbnailer(source).get_thumbnail(opts)

    def delete_thumbnails(self, source):
        from easy_thumbnails.files import get_thumbnailer
        get_thumbnailer(source).delete(save=False)


def get_thumbnailer():
    thumbnailer = import_string(settings.OSCAR_THUMBNAILER)
    return thumbnailer()
