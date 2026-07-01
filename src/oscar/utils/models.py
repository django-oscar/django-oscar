import datetime
import posixpath

from django.conf import settings


# pylint: disable=unused-argument
def get_image_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_FOLDER), filename
    )
