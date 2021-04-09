from unittest import mock

from django.apps import apps
from django.test import TestCase
from django.test.utils import modify_settings
from django.urls import path
from django.views.generic import View

from oscar.core.application import AutoLoadURLsConfigMixin


class AutoLoadURLsConfig(AutoLoadURLsConfigMixin):
    def __init__(self):
        self._create_required_attributes()


class TestAutoLoadURLsConfigMixin:
    wishlist_app_config = 'oscar.apps.wishlists.apps.WishlistsConfig'
    reviews_app_config = 'oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig'

    @mock.patch('oscar.core.application.AutoLoadURLsConfigMixin._create_required_attributes')
    @mock.patch('oscar.core.application.AutoLoadURLsConfigMixin.get_app_label_url_endpoint_mapping')
    def test_ready_is_called_once_if_get_auto_loaded_urls_is_called_before_it(self, mocked_mapping,
                                                                              mocked_create_required_attributes):
        mocked_mapping.return_value = {"reviews": "reviews/", "wishlists": "wishlists/"}
        config = AutoLoadURLsConfig()
        try:
            config.get_auto_loaded_urls()
        except AttributeError:
            pass  # un-mocked `config.ready` method is required to create the missing attribute(s)
        mocked_create_required_attributes.assert_called_once()

    @mock.patch('oscar.core.application.AutoLoadURLsConfigMixin.get_app_label_url_endpoint_mapping')
    def test_get_auto_loaded_urls_for_installed_app(self, mocked_mapping, settings):
        mocked_mapping.return_value = {"reviews": "reviews/", "wishlists": "wishlists/"}
        config = AutoLoadURLsConfig()

        assert self.reviews_app_config in settings.INSTALLED_APPS
        assert self.wishlist_app_config in settings.INSTALLED_APPS
        assert len(config.get_auto_loaded_urls()) == 2

    @mock.patch('oscar.core.application.AutoLoadURLsConfigMixin.get_app_label_url_endpoint_mapping')
    def test_get_auto_loaded_urls_for_un_installed_app(self, mocked_mapping, settings):
        mocked_mapping.return_value = {"reviews": "reviews/", "wishlists": "wishlists/"}
        installed_apps = settings.INSTALLED_APPS.copy()
        installed_apps.remove(self.reviews_app_config)
        installed_apps.remove(self.wishlist_app_config)

        settings.INSTALLED_APPS = installed_apps

        config = AutoLoadURLsConfig()
        assert len(config.get_auto_loaded_urls()) == 0


@modify_settings(INSTALLED_APPS={
    'append': 'tests._site.apps.myapp.apps.TestConfig',
})
class OscarConfigTestCase(TestCase):

    def setUp(self):
        self.myapp = apps.get_app_config('myapp')

    def test_get_permissions_required_uses_map(self):
        perms = self.myapp.get_permissions('index')
        self.assertEqual(perms, 'is_staff')

    def test_permissions_required_falls_back_to_default(self):
        perms = self.myapp.get_permissions('notinmap')
        self.assertEqual(perms, 'is_superuser')

    @mock.patch('oscar.views.decorators.permissions_required')
    def test_get_url_decorator_fetches_correct_perms(self, mock_permissions_required):
        pattern = path('', View.as_view(), name='index')
        self.myapp.get_url_decorator(pattern)
        mock_permissions_required.assert_called_once_with('is_staff', login_url=None)

    def test_post_process_urls_adds_decorator(self):
        def fake_callback():
            pass

        fake_decorator = mock.Mock()
        fake_decorator.return_value = fake_callback

        self.myapp.get_url_decorator = mock.Mock()
        self.myapp.get_url_decorator.return_value = fake_decorator

        pattern = path('', View.as_view(), name='index')
        processed_patterns = self.myapp.post_process_urls([pattern])

        self.myapp.get_url_decorator.assert_called_once_with(pattern)
        self.assertEqual(processed_patterns[0].callback, fake_callback)
