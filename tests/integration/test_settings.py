from django.conf import settings
from django.test import TestCase


class TestOscarInstalledAppsList(TestCase):
    def test_includes_oscar_itself(self):
        installed_apps = settings.INSTALLED_APPS
        self.assertTrue("oscar.config.Shop" in installed_apps)
