from django.conf import settings
from django.test import TestCase
from django.template import loader, TemplateDoesNotExist


class TestOscarInstalledAppsList(TestCase):

    def test_includes_oscar_itself(self):
        installed_apps = settings.INSTALLED_APPS
        self.assertTrue('oscar' in installed_apps)


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
        rendered_template = template.render({})
        self.assertIn('Oscar Test Shop', rendered_template)

    def test_default_oscar_templates_are_accessible(self):
        path = 'oscar/base.html'
        template = loader.get_template(path)
        rendered_template = template.render({})
        self.assertNotIn('Oscar Test Shop', rendered_template)
