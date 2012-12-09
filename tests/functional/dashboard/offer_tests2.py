from django.core.urlresolvers import reverse
from oscar_testsupport import testcases

from oscar.apps.offer import models


class TestAnAdmin(testcases.WebTestCase):
    # New version of offer tests buy using WebTest
    is_staff = True

    def setUp(self):
        super(TestAnAdmin, self).setUp()
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True)

    def test_can_create_an_offer(self):
        list_page = self.get(reverse('dashboard:offer-list'))

        metadata_page = list_page.click('Create new offer')
        metadata_form = metadata_page.form
        metadata_form['name'] = "Test offer"
        metadata_form['start_date'] = "2012-01-01"
        metadata_form['end_date'] = "2014-01-01"

        condition_page = metadata_form.submit().follow()
        condition_form = condition_page.form
        condition_form['range'] = self.range.id
        condition_form['type'] = "Count"
        condition_form['value'] = "3"

        benefit_page = condition_form.submit().follow()
        benefit_form = benefit_page.form
        benefit_form['range'] = self.range.id
        benefit_form['type'] = "Percentage"
        benefit_form['value'] = "25"

        preview_page = benefit_form.submit().follow()
        preview_page.form.submit()

        offers = models.ConditionalOffer.objects.all()
        self.assertEqual(1, len(offers))
        offer = offers[0]
        self.assertEqual("Test offer", offer.name)
        self.assertEqual(3, offer.condition.value)
        self.assertEqual(25, offer.benefit.value)

    def test_cannot_jump_to_intermediate_step(self):
        for url_name in ('dashboard:offer-condition',
                         'dashboard:offer-benefit',
                         'dashboard:offer-preview'):
            response = self.get(reverse(url_name))
            self.assertEqual(302, response.status_code)
