import datetime

from django.test import TestCase
from django.utils.timezone import now

from oscar.apps.dashboard.offers import forms


class TestRestrictionsFormEnforces(TestCase):

    def test_cronological_dates(self):
        start = now()
        end = start - datetime.timedelta(days=30)
        post = {'name': 'dummy',
                'description': 'dummy',
                'start_datetime': start,
                'end_datetime': end}
        form = forms.RestrictionsForm(post)
        self.assertFalse(form.is_valid())
