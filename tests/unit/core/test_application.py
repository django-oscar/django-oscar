from unittest import mock

from django.apps import apps
from django.test import TestCase
from django.test.utils import modify_settings
from django.urls import path
from django.views.generic import View


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
