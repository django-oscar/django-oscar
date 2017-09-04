from django import VERSION as DJANGO_VERSION
from django import forms
from django.test import override_settings

from oscar.core.loading import get_class
from oscar.test.factories import Member
from oscar.test.testcases import WebTestCase

RelatedFieldWidgetWrapper = get_class('dashboard.widgets',
                                      'RelatedFieldWidgetWrapper')


@override_settings(ROOT_URLCONF='oscar.test.factories.urls')
class RelatedFieldWidgetWrapperTests(WebTestCase):

    def test_custom_widget_render(self):
        class CustomWidget(forms.Select):
            def render(self, *args, **kwargs):
                return 'custom render output'
        # The "Field.rel" attribute was renamed to "remote_field" in Django 1.9
        # Documentation URL: <https://docs.djangoproject.com/en/1.11/releases/1.9/#field-rel-changes>
        if DJANGO_VERSION < (1, 9):
            rel = Member._meta.get_field('band').rel
        else:
            rel = Member._meta.get_field('band').remote_field
        widget = CustomWidget()
        wrapper = RelatedFieldWidgetWrapper(widget, rel)
        output = wrapper.render('name', 'value')
        self.assertIn('custom render output', output)

    def test_widget_delegates_value_omitted_from_data(self):
        class CustomWidget(forms.Select):
            def value_omitted_from_data(self, data, files, name):
                return False
        # The "Field.rel" attribute was renamed to "remote_field" in Django 1.9
        # Documentation URL: <https://docs.djangoproject.com/en/1.11/releases/1.9/#field-rel-changes>
        if DJANGO_VERSION < (1, 9):
            rel = Member._meta.get_field('band').rel
        else:
            rel = Member._meta.get_field('band').remote_field
        widget = CustomWidget()
        wrapper = RelatedFieldWidgetWrapper(widget, rel)
        self.assertIs(wrapper.value_omitted_from_data({}, {}, 'band'), False)

    def test_widget_render(self):
        # The "Field.rel" attribute was renamed to "remote_field" in Django 1.9
        # Documentation URL: <https://docs.djangoproject.com/en/1.11/releases/1.9/#field-rel-changes>
        if DJANGO_VERSION < (1, 9):
            rel = Member._meta.get_field('band').rel
        else:
            rel = Member._meta.get_field('band').remote_field
        widget = forms.Select()
        wrapper = RelatedFieldWidgetWrapper(widget, rel)
        context = wrapper.get_context('name', 'value', None)
        self.assertTrue(context, 'rendered_widget')
        self.assertTrue(context, 'name')
        self.assertTrue(context, 'url_params')
        self.assertTrue(context, 'model')
        self.assertTrue(context, 'add_related_url')
        self.assertTrue(context, 'change_related_template_url')
        self.assertTrue(context, 'delete_related_template_url')
