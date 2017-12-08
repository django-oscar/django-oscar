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

        remote_field = Member._meta.get_field('band').remote_field
        widget = CustomWidget()
        wrapper = RelatedFieldWidgetWrapper(widget, remote_field)
        output = wrapper.render('name', 'value')
        self.assertIn('custom render output', output)

    def test_widget_delegates_value_omitted_from_data(self):
        class CustomWidget(forms.Select):
            def value_omitted_from_data(self, data, files, name):
                return False

        remote_field = Member._meta.get_field('band').remote_field
        widget = CustomWidget()
        wrapper = RelatedFieldWidgetWrapper(widget, remote_field)
        self.assertIs(wrapper.value_omitted_from_data({}, {}, 'band'), False)

    def test_widget_render(self):
        remote_field = Member._meta.get_field('band').remote_field
        widget = forms.Select()
        wrapper = RelatedFieldWidgetWrapper(widget, remote_field)
        context = wrapper.get_context('name', 'value', None)
        self.assertTrue(context, 'rendered_widget')
        self.assertTrue(context, 'name')
        self.assertTrue(context, 'url_params')
        self.assertTrue(context, 'model')
        self.assertTrue(context, 'add_related_url')
        self.assertTrue(context, 'change_related_template_url')
        self.assertTrue(context, 'delete_related_template_url')
