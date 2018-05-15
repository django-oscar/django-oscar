import mock

from django.conf.urls import url
from django.test import TestCase
from django.views.generic import View

from tests._site.apps.myapp.app import application


class ApplicationTestCase(TestCase):

    def test_get_permissions_required_uses_map(self):
        perms = application.get_permissions('index')
        self.assertEqual(perms, 'is_staff')

    def test_permissions_required_falls_back_to_default(self):
        perms = application.get_permissions('notinmap')
        self.assertEqual(perms, 'is_superuser')

    @mock.patch('oscar.core.application.permissions_required')
    def test_get_url_decorator_fetches_correct_perms(self, mock_permissions_required):
        pattern = url('^$', View.as_view(), name='index')
        application.get_url_decorator(pattern)
        mock_permissions_required.assert_called_once_with('is_staff', login_url=None)

    def test_post_process_urls_adds_decorator(self):
        fake_decorator = mock.Mock()
        fake_decorator.return_value = 'fake_callback'

        application.get_url_decorator = mock.Mock()
        application.get_url_decorator.return_value = fake_decorator

        pattern = url('^$', View.as_view(), name='index')
        processed_patterns = application.post_process_urls([pattern])

        application.get_url_decorator.assert_called_once_with(pattern)
        self.assertEqual(processed_patterns[0].callback, 'fake_callback')
