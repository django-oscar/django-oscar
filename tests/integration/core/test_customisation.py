import pytest
from django.conf import settings
from django.test import TestCase

from oscar.core import customisation

VALID_FOLDER_PATH = 'tests/_site/apps'


class TestUtilities(TestCase):

    def test_subfolder_extraction(self):
        folders = list(customisation.subfolders('/var/www/eggs'))
        self.assertEqual(folders, ['/var', '/var/www', '/var/www/eggs'])


def test_raises_exception_for_nonexistant_app_label():
    with pytest.raises(ValueError):
        customisation.fork_app('sillytown', 'somefolder')


def test_raises_exception_if_app_has_already_been_forked():
    # We piggyback on another test which means a custom app is already in
    # the settings we use for the test suite. We just check that's still
    # the case here.
    assert 'tests._site.apps.partner' in settings.INSTALLED_APPS
    with pytest.raises(ValueError):
        customisation.fork_app('partner', VALID_FOLDER_PATH)


def test_creates_new_folder(tmpdir):
    path = tmpdir.mkdir('fork')
    customisation.fork_app('order', str(path))
    path.join('order').ensure_dir()


def test_creates_init_file(tmpdir):
    path = tmpdir.mkdir('fork')
    customisation.fork_app('order', str(path))

    path.join('order').join('__init__.py').ensure()


def test_handles_dashboard_app(tmpdir):
    # Dashboard apps are fiddly as they aren't identified by a single app
    # label.
    path = tmpdir.mkdir('fork')
    customisation.fork_app('dashboard.catalogue', str(path))
    # Check __init__.py created (and supporting folders)

    path.join('dashboard').join('catalogue').join('__init__.py').ensure()


def test_creates_models_and_admin_file(tmpdir):
    path = tmpdir.mkdir('fork')
    customisation.fork_app('order', str(path))
    for module, expected_string in [
        ('models', 'from oscar.apps.order.models import *'),
        ('admin', 'from oscar.apps.order.admin import *'),
        ('config', 'OrderConfig')
    ]:
        filepath = path.join('order').join('%s.py' % module)
        filepath.ensure()
        contents = filepath.read()
        assert expected_string in contents


def test_copies_in_migrations_when_needed(tmpdir):
    path = tmpdir.mkdir('fork')
    for app, has_models in [('order', True), ('search', False)]:
        customisation.fork_app(app, str(path))

        native_migration_path = path.join(app).join('migrations')
        assert has_models == native_migration_path.check()


def test_dashboard_app_config(tmpdir, monkeypatch):
    path = tmpdir.mkdir('fork')
    customisation.fork_app('dashboard', str(path))

    path.join('__init__.py').write('')
    monkeypatch.syspath_prepend(str(tmpdir))

    config_module = __import__(
        '%s.dashboard.config' % path.basename, fromlist=['DashboardConfig']
    )

    assert hasattr(config_module, 'DashboardConfig')
