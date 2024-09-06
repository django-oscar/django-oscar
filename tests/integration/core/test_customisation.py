import os
import sys
import tempfile
from pathlib import Path
from os.path import exists, join

import pytest
from django.conf import settings
from django.test import TestCase, override_settings

from oscar.core import customisation
from tests import delete_from_import_cache

VALID_FOLDER_PATH = str(
    (Path(__file__).parent.parent.parent.parent / "tests/_site/apps").absolute()
)


class TestUtilities(TestCase):
    def test_subfolder_extraction(self):
        folders = list(customisation.subfolders("/var/www/eggs"))
        self.assertEqual(folders, ["/var", "/var/www", "/var/www/eggs"])


def test_raises_exception_for_nonexistant_app_label():
    with pytest.raises(ValueError):
        customisation.fork_app("sillytown", "somefolder", "sillytown")


def test_raises_exception_if_app_has_already_been_forked():
    # We piggyback on another test which means a custom app is already in
    # the apps directory we use for the test suite. We just check that's still
    # the case here.
    assert exists(join(VALID_FOLDER_PATH, "partner"))
    with pytest.raises(ValueError):
        customisation.fork_app("partner", VALID_FOLDER_PATH, "partner")


def test_creates_new_folder(tmpdir):
    path = tmpdir.mkdir("fork")
    customisation.fork_app("order", str(path), "order")
    path.join("order").ensure_dir()


def test_creates_init_file(tmpdir, monkeypatch):
    path = tmpdir.mkdir("fork")
    customisation.fork_app("order", str(path), "order")

    path.join("order").join("__init__.py").ensure()

    monkeypatch.syspath_prepend(str(tmpdir))

    config_module = __import__("fork.order.apps", fromlist=["OrderConfig"])
    delete_from_import_cache("fork.order.apps")

    expected_string = "default_app_config = '{}.apps.OrderConfig".format(
        config_module.OrderConfig.name
    )
    contents = path.join("order").join("__init__.py").read()
    assert expected_string in contents


def test_handles_dashboard_app(tmpdir):
    # Dashboard apps are fiddly as they aren't identified by a single app
    # label.
    path = tmpdir.mkdir("fork")
    customisation.fork_app("catalogue_dashboard", str(path), "dashboard.catalogue")
    # Check __init__.py created (and supporting folders)

    path.join("dashboard").join("catalogue").join("__init__.py").ensure()


def test_creates_models_and_admin_file(tmpdir):
    path = tmpdir.mkdir("fork")
    customisation.fork_app("order", str(path), "order")
    for module, expected_string in [
        ("models", "from oscar.apps.order.models import *"),
        ("admin", "from oscar.apps.order.admin import *"),
        ("apps", "OrderConfig"),
    ]:
        filepath = path.join("order").join("%s.py" % module)
        filepath.ensure()
        contents = filepath.read()
        assert expected_string in contents


def test_copies_in_migrations_when_needed(tmpdir):
    path = tmpdir.mkdir("fork")
    for app, has_models in [("order", True), ("search", False)]:
        customisation.fork_app(app, str(path), app)

        native_migration_path = path.join(app).join("migrations")
        assert has_models == native_migration_path.check()


def test_dashboard_app_config(tmpdir, monkeypatch):
    path = tmpdir.mkdir("fork")
    customisation.fork_app("dashboard", str(path), "dashboard")

    path.join("__init__.py").write("")
    monkeypatch.syspath_prepend(str(tmpdir))

    config_module = __import__(
        "%s.dashboard.apps" % path.basename, fromlist=["DashboardConfig"]
    )

    assert hasattr(config_module, "DashboardConfig")


class TestForkApp(TestCase):
    def setUp(self):
        self.original_paths = sys.path[:]
        sys.path.append("./tests/_site/")

    def tearDown(self):
        sys.path = self.original_paths

    def test_fork_third_party(self):
        tmpdir = tempfile.mkdtemp()
        installed_apps = list(settings.INSTALLED_APPS)
        installed_apps.append("thirdparty_package.apps.myapp.apps.MyAppConfig")
        with override_settings(INSTALLED_APPS=installed_apps):
            customisation.fork_app("myapp", tmpdir, "custom_myapp")
            forked_app_dir = join(tmpdir, "custom_myapp")
            assert exists(forked_app_dir)
            assert exists(join(forked_app_dir, "apps.py"))
            sys.path.append(tmpdir)

            config_module = __import__(
                "custom_myapp.apps", fromlist=["CustomMyAppConfig"]
            )
            assert hasattr(config_module, "MyAppConfig")
            assert config_module.MyAppConfig.name.endswith(".custom_myapp")

    def test_absolute_target_path(self):
        tmpdir = tempfile.mkdtemp()
        customisation.fork_app("order", tmpdir, "order")
        sys.path.append(tmpdir)
        config_module = __import__("order.apps", fromlist=["OrderConfig"])
        assert hasattr(config_module, "OrderConfig")
        config_app_name = config_module.OrderConfig.name
        assert not config_app_name.startswith(".")

    def test_local_folder(self):
        tmpdir = tempfile.mkdtemp()
        os.chdir(tmpdir)
        customisation.fork_app("basket", ".", "basket")
        sys.path.append(tmpdir)
        config_module = __import__("basket.apps", fromlist=["BasketConfig"])
        assert hasattr(config_module, "BasketConfig")
        assert config_module.BasketConfig.name == "basket"
