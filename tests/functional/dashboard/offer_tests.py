import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase

from oscar_testsupport.testcases import ClientTestCase
from oscar.apps.offer.models import Range, ConditionalOffer, Condition, Benefit
from oscar.apps.dashboard.offers.forms import MetaDataForm


class ViewTests(ClientTestCase):
    is_staff = True

    def test_pages_exist(self):
        urls = [reverse('dashboard:offer-list'),
                reverse('dashboard:offer-metadata'),
               ]
        for url in urls:
            self.assertIsOk(self.client.get(url))


class MetadataFormTests(TestCase):

    def test_dates_must_be_cronological(self):
        start_date = datetime.date(2012, 1, 1)
        end_date = datetime.date(2011, 1, 1)
        post = {'name': 'dummy',
                'description': 'dummy',
                'start_date': start_date,
                'end_date': end_date,}
        form = MetaDataForm(post)
        self.assertFalse(form.is_valid())


class OfferUpdatingTests(ClientTestCase):
    is_staff = True

    def setUp(self):
        super(OfferUpdatingTests, self).setUp()
        self.range = Range.objects.create(name='All products',
                                          includes_all_products=True)
        condition = Condition.objects.create(range=self.range,
                                             type='Count',
                                             value=3)
        benefit = Benefit.objects.create(range=self.range,
                                         type='Multibuy',
                                         value=1)

        start_date = datetime.date(2012, 1, 1)
        end_date = datetime.date(2013, 1, 1)
        self.offer = ConditionalOffer.objects.create(name='my offer',
                                                     description='something',
                                                     start_date=start_date,
                                                     end_date=end_date,
                                                     condition=condition,
                                                     benefit=benefit)

    def tearDown(self):
        ConditionalOffer.objects.all().delete()

    def test_happy_path(self):
        metadata_url = reverse('dashboard:offer-metadata', kwargs={'pk': self.offer.id})
        response = self.client.get(metadata_url)
        self.assertTrue('my offer' in response.content)

        response = self.client.post(metadata_url,
                                    {'name': 'my new offer',
                                     'description': 'something',
                                     'start_date': '2012-01-01',
                                     'end_date': '2013-01-01'})
        self.assertIsRedirect(response)

        condition_url = reverse('dashboard:offer-condition', kwargs={'pk': self.offer.id})
        response = self.client.post(condition_url,
                                    {'range': self.range.id,
                                     'type': 'Count',
                                     'value': '3',})
        self.assertIsRedirect(response)

        benefit_url = reverse('dashboard:offer-benefit', kwargs={'pk': self.offer.id})
        response = self.client.post(benefit_url,
                                    {'range': self.range.id,
                                     'type': 'Multibuy',
                                     'value': '',})
        self.assertIsRedirect(response)

        preview_url = reverse('dashboard:offer-preview', kwargs={'pk': self.offer.id})
        response = self.client.get(preview_url)
        self.assertTrue('my new offer' in response.content)

        response = self.client.post(preview_url)
        self.assertIsRedirect(response)

        offer = ConditionalOffer.objects.get(id=self.offer.id)
        self.assertEqual('my new offer', offer.name)

    def test_can_jump_to_condition_step(self):
        response = self.client.get(reverse('dashboard:offer-condition',
                                           kwargs={'pk': self.offer.id}))
        self.assertIsOk(response)
