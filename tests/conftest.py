import os
import shutil
import warnings

import django


def pytest_addoption(parser):
    parser.addoption("--sqlite", action="store_true")
    parser.addoption("--deprecation", choices=["strict", "log", "none"], default="log")


def pytest_configure(config):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

    deprecation = config.getoption("deprecation")
    if deprecation == "strict":
        warnings.simplefilter("error", DeprecationWarning)
        warnings.simplefilter("error", PendingDeprecationWarning)
        warnings.simplefilter("error", RuntimeWarning)
    if deprecation == "log":
        warnings.simplefilter("always", DeprecationWarning)
        warnings.simplefilter("always", PendingDeprecationWarning)
        warnings.simplefilter("always", RuntimeWarning)
    elif deprecation == "none":
        # Deprecation warnings are ignored by default
        pass

    if config.getoption("sqlite"):
        os.environ["DATABASE_ENGINE"] = "django.db.backends.sqlite3"
        os.environ["DATABASE_NAME"] = ":memory:"

    django.setup()


# pylint: disable=unused-argument
def pytest_unconfigure(config):
    # remove tests/public/media folder
    from django.conf import settings

    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
