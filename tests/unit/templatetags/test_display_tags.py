from django.test import RequestFactory, TestCase

from oscar.templatetags.display_tags import get_parameters


class DisplayTagsTestCase(TestCase):
    def test_get_parameters_strips_except_field(self):
        ctx = {"request": RequestFactory().get("/?foo=bar&bar=baz")}
        self.assertEqual(get_parameters(ctx, "foo"), "bar=baz&")
        self.assertEqual(get_parameters(ctx, "bar"), "foo=bar&")
        self.assertEqual(get_parameters(ctx, "invalid"), "foo=bar&bar=baz&")

    def test_get_parameters_returns_empty_string_if_no_params_left(self):
        ctx = {"request": RequestFactory().get("/?foo=bar")}
        self.assertEqual(get_parameters(ctx, "foo"), "")
