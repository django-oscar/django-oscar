from django.test import TestCase

import oscar


class OscarTests(TestCase):

    def test_app_list_exists(self):
        core_apps = oscar.OSCAR_CORE_APPS
        self.assertTrue('oscar' in core_apps)

    def test_app_list_can_be_accessed_through_fn(self):
        core_apps = oscar.get_core_apps()
        self.assertTrue('oscar' in core_apps)

    def test_app_list_can_be_accessed_with_overrides(self):
        apps = oscar.get_core_apps(overrides=['apps.shipping'])
        self.assertTrue('apps.shipping' in apps)
        self.assertTrue('oscar.apps.shipping' not in apps)
