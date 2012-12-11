import datetime

from django.test import TestCase

from oscar.apps.dashboard.offers import forms


class TestRestrictionsFormEnforces(TestCase):

    def test_cronological_dates(self):
        start_date = datetime.date(2012, 1, 1)
        end_date = datetime.date(2011, 1, 1)
        post = {'name': 'dummy',
                'description': 'dummy',
                'start_date': start_date,
                'end_date': end_date}
        form = forms.RestrictionsForm(post)
        self.assertFalse(form.is_valid())
