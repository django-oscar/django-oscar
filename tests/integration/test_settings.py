from django.test import TestCase
from django.template import loader, Context, TemplateDoesNotExist

import oscar


class TestOscarCoreAppsList(TestCase):

    def test_includes_oscar_itself(self):
        core_apps = oscar.OSCAR_CORE_APPS
        self.assertTrue('oscar' in core_apps)

    def test_can_be_retrieved_through_fn(self):
        core_apps = oscar.get_core_apps()
        self.assertTrue('oscar' in core_apps)

    def test_can_be_retrieved_with_overrides(self):
        apps = oscar.get_core_apps(overrides=['apps.shipping'])
        self.assertTrue('apps.shipping' in apps)
        self.assertTrue('oscar.apps.shipping' not in apps)

    def test_raises_exception_for_string_arg(self):
        with self.assertRaises(ValueError):
            oscar.get_core_apps('forks.catalogue')


class TestOscarTemplateSettings(TestCase):
    """
    Oscar's OSCAR_MAIN_TEMPLATE_DIR setting
    """
    def test_allows_a_template_to_be_accessed_via_two_paths(self):
        paths = ['base.html', 'oscar/base.html']
        for path in paths:
            try:
                loader.get_template(path)
            except TemplateDoesNotExist:
                self.fail("Template %s should exist" % path)

    def test_allows_a_template_to_be_customized(self):
        path = 'base.html'
        template = loader.get_template(path)
        rendered_template = template.render(Context())
        self.assertIn('Oscar Test Shop', rendered_template)

    def test_default_oscar_templates_are_accessible(self):
        path = 'oscar/base.html'
        template = loader.get_template(path)
        rendered_template = template.render(Context())
        self.assertNotIn('Oscar Test Shop', rendered_template)
