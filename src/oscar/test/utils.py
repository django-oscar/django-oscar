import queue
import os
import shutil
import threading
from datetime import date

from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import Signer
from django.db import connection
from django.test import RequestFactory as BaseRequestFactory

from oscar.core.loading import get_class, get_model
from oscar.core.thumbnails import get_thumbnailer
from oscar.test.factories import ProductImageFactory
from sorl.thumbnail.conf import settings as sorl_settings


OSCAR_IMAGE_FOLDER_FORMATTED = 'images/products/{0}/{1:02d}/'.format(date.today().year, date.today().month)
FULL_PATH_TO_IMAGES_FOLDER = os.path.join(settings.MEDIA_ROOT, OSCAR_IMAGE_FOLDER_FORMATTED)
FULL_PATH_TO_SORL_THUMBNAILS_FOLDER = os.path.join(settings.MEDIA_ROOT, sorl_settings.THUMBNAIL_PREFIX)
EASY_THUMBNAIL_BASEDIR = 'thumbnails'
FULL_PATH_TO_EASY_THUMBNAILS_FOLDER = os.path.join(
    settings.MEDIA_ROOT, EASY_THUMBNAIL_BASEDIR, OSCAR_IMAGE_FOLDER_FORMATTED)


def remove_image_folders():
    if os.path.exists(FULL_PATH_TO_IMAGES_FOLDER):
        shutil.rmtree(FULL_PATH_TO_IMAGES_FOLDER)
    if os.path.exists(FULL_PATH_TO_SORL_THUMBNAILS_FOLDER):
        shutil.rmtree(FULL_PATH_TO_SORL_THUMBNAILS_FOLDER)
    if os.path.exists(FULL_PATH_TO_EASY_THUMBNAILS_FOLDER):
        shutil.rmtree(FULL_PATH_TO_EASY_THUMBNAILS_FOLDER)


def get_thumbnail_full_path(thumbnail_url):
    # Thumbnail URL looks like "/media/...........jpg". To be able to
    # create full path we need to remove the first "/" from it.
    return os.path.join(settings.PUBLIC_ROOT, thumbnail_url[1:])


class ThumbnailMixin:

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Remove images folders - they could be created in the previous tests.
        remove_image_folders()

    def setUp(self):
        super().setUp()
        self.thumbnail_options = {
            'size': 'x50',
            'upscale': False,
        }

    def tearDown(self):
        super().tearDown()
        # Remove created images folders after each test.
        remove_image_folders()

    def create_product_images(self, qty=2, product=None):
        self._test_images_folder_is_empty()

        kwargs = {}
        if product is not None:
            kwargs['product'] = product
        self.images = ProductImageFactory.create_batch(qty, **kwargs)

        file_names = os.listdir(FULL_PATH_TO_IMAGES_FOLDER)
        assert len(file_names) == qty  # New images added.

    def create_thumbnails(self):
        thumbnailer = get_thumbnailer()
        thumbnails_full_paths = []

        for image in self.images:
            thumbnail = thumbnailer.generate_thumbnail(image.original, **self.thumbnail_options)
            thumbnails_full_paths.append(get_thumbnail_full_path(thumbnail.url))

        # Check thumbnails exist in the file system.
        for path in thumbnails_full_paths:
            assert os.path.isfile(path)  # `isfile` returns `True` if path is an existing regular file.

        return thumbnails_full_paths

    def _test_images_folder_is_empty(self):
        if not os.path.exists(FULL_PATH_TO_IMAGES_FOLDER):
            os.makedirs(FULL_PATH_TO_IMAGES_FOLDER)

        file_names = os.listdir(FULL_PATH_TO_IMAGES_FOLDER)
        assert len(file_names) == 0

    def _test_thumbnails_not_exist(self, thumbnails_full_paths):
        for path in thumbnails_full_paths:
            assert not os.path.isfile(path)


class RequestFactory(BaseRequestFactory):
    Basket = get_model('basket', 'basket')
    selector = get_class('partner.strategy', 'Selector')()

    def request(self, user=None, basket=None, **request):
        request = super().request(**request)
        request.user = user or AnonymousUser()
        request.session = SessionStore()
        request._messages = FallbackStorage(request)

        # Mimic basket middleware
        request.strategy = self.selector.strategy(
            request=request, user=request.user)
        request.basket = basket or self.Basket()
        request.basket.strategy = request.strategy
        request.basket_hash = Signer().sign(basket.pk) if basket else None
        request.cookies_to_delete = []

        return request


def run_concurrently(fn, kwargs=None, num_threads=5):
    exceptions = queue.Queue()

    def worker(**kwargs):
        try:
            fn(**kwargs)
        except Exception as exc:
            exceptions.put(exc)
        else:
            exceptions.put(None)
        finally:
            connection.close()

    kwargs = kwargs if kwargs is not None else {}

    # Run them
    threads = [
        threading.Thread(target=worker, name='thread-%d' % i, kwargs=kwargs)
        for i in range(num_threads)
    ]
    try:
        for thread in threads:
            thread.start()
    finally:
        for thread in threads:
            thread.join()

    # Retrieve exceptions
    exceptions = [exceptions.get(block=False) for i in range(num_threads)]
    return [exc for exc in exceptions if exc is not None]
