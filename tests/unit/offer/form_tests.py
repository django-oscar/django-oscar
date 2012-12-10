import datetime

from django.test import TestCase

from oscar.apps.dashboard.offers.forms import MetaDataForm


class TestMetadataFormEnforces(TestCase):

    def test_cronological_dates(self):
        start_date = datetime.date(2012, 1, 1)
        end_date = datetime.date(2011, 1, 1)
        post = {'name': 'dummy',
                'description': 'dummy',
                'start_date': start_date,
                'end_date': end_date}
        form = MetaDataForm(post)
        self.assertFalse(form.is_valid())
