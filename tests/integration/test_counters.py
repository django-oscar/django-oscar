from django import test
from django import template


class CountersOnMainPageTests(test.TestCase):

    def setUp(self):
        self.response = self.client.get('/')

    def _test(self, key, default_value):
        self.assertIn(key, self.response.context)
        self.assertEquals(self.response.context[key], default_value)

    def test_counters_settings_in_context(self):
        self._test('counters_settings', {})

    def test_counters_templates_in_context(self):
        self._test('counters_templates',
                   ['oscar/partials/google_analytics.html'])
