import os
import tempfile

from django.test import TestCase
from django.conf import settings

from oscar.core import customisation

VALID_FOLDER_PATH = 'tests/_site/apps'


class TestForkAppFunction(TestCase):

    def setUp(self):
        self.tmp_folder = tempfile.mkdtemp()

    def test_raises_exception_for_nonexistant_app_label(self):
        with self.assertRaises(ValueError):
            customisation.fork_app('sillytown', 'somefolder')

    def test_raises_exception_for_nonexistant_folder(self):
        assert not os.path.exists('does_not_exist')
        with self.assertRaises(ValueError):
            customisation.fork_app('order', 'does_not_exist')

    def test_raises_exception_if_app_has_alredy_been_forked(self):
        # We piggyback on another test which means a custom app is already in
        # the settings we use for the test suite. We just check that's still
        # the case here.
        assert 'tests._site.apps.partner' in settings.INSTALLED_APPS
        with self.assertRaises(ValueError):
            customisation.fork_app('partner', VALID_FOLDER_PATH)

    def test_creates_new_folder(self):
        customisation.fork_app('order', self.tmp_folder)
        new_folder_path = os.path.join(self.tmp_folder, 'order')
        self.assertTrue(os.path.exists(new_folder_path))

    def test_creates_init_file(self):
        customisation.fork_app('order', self.tmp_folder)
        filepath = os.path.join(self.tmp_folder, 'order', '__init__.py')
        self.assertTrue(os.path.exists(filepath))

    def test_creates_models_file(self):
        customisation.fork_app('order', self.tmp_folder)
        filepath = os.path.join(self.tmp_folder, 'order', 'models.py')
        self.assertTrue(os.path.exists(filepath))

        contents = open(filepath).read()
        self.assertTrue('from oscar.apps.order.models import *' in contents)

    def test_copies_in_migrations(self):
        customisation.fork_app('order', self.tmp_folder)
        migration_path = os.path.join(self.tmp_folder, 'order', 'migrations')
        self.assertTrue(os.path.exists(migration_path))
