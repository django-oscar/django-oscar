from django.urls import reverse
from django.utils import timezone

from oscar.apps.offer import models
from oscar.test import factories, testcases


class TestAnAdmin(testcases.WebTestCase):
    # New version of offer tests buy using WebTest
    is_staff = True

    def setUp(self):
        super().setUp()
        self.range = models.Range.objects.create(
            name="All products", includes_all_products=True)

    def test_can_create_an_offer(self):
        list_page = self.get(reverse('dashboard:offer-list'))

        metadata_page = list_page.click('Create new offer')
        metadata_form = metadata_page.form
        metadata_form['name'] = "Test offer"

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form
        benefit_form['range'] = self.range.id
        benefit_form['type'] = "Percentage"
        benefit_form['value'] = "25"

        condition_page = benefit_form.submit().follow()
        condition_form = condition_page.form
        condition_form['range'] = self.range.id
        condition_form['type'] = "Count"
        condition_form['value'] = "3"

        restrictions_page = condition_form.submit().follow()
        restrictions_page.form.submit()

        offers = models.ConditionalOffer.objects.all()
        self.assertEqual(1, len(offers))
        offer = offers[0]
        self.assertEqual("Test offer", offer.name)
        self.assertEqual(3, offer.condition.value)
        self.assertEqual(25, offer.benefit.value)

    def test_offer_list_page(self):
        offer = factories.create_offer(name="Offer A")

        list_page = self.get(reverse('dashboard:offer-list'))
        form = list_page.forms[0]
        form['name'] = "I do not exist"
        res = form.submit()
        self.assertTrue("No offers found" in res.text)

        form['name'] = "Offer A"
        res = form.submit()
        self.assertFalse("No offers found" in res.text)

        form['is_active'] = True
        res = form.submit()
        self.assertFalse("No offers found" in res.text)

        yesterday = timezone.now() - timezone.timedelta(days=1)
        offer.end_datetime = yesterday
        offer.save()

        form['is_active'] = True
        res = form.submit()
        self.assertTrue("No offers found" in res.text)

    def test_can_update_an_existing_offer(self):
        factories.create_offer(name="Offer A")

        list_page = self.get(reverse('dashboard:offer-list'))
        detail_page = list_page.click('Offer A')

        metadata_page = detail_page.click(linkid="edit_metadata")
        metadata_form = metadata_page.form
        metadata_form['name'] = "Offer A+"

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form

        condition_page = benefit_form.submit().follow()
        condition_form = condition_page.form

        restrictions_page = condition_form.submit().follow()
        restrictions_page.form.submit()

        models.ConditionalOffer.objects.get(name="Offer A+")

    def test_can_update_an_existing_offer_save_directly(self):
        # see if we can save the offer directly without completing all
        # steps
        offer = factories.create_offer(name="Offer A")
        name_and_description_page = self.get(
            reverse('dashboard:offer-metadata', kwargs={'pk': offer.pk}))
        res = name_and_description_page.form.submit('save').follow()
        self.assertEqual(200, res.status_code)

    def test_can_jump_to_intermediate_step_for_existing_offer(self):
        offer = factories.create_offer()
        url = reverse('dashboard:offer-condition',
                      kwargs={'pk': offer.id})
        self.assertEqual(200, self.get(url).status_code)

    def test_cannot_jump_to_intermediate_step(self):
        for url_name in ('dashboard:offer-condition',
                         'dashboard:offer-benefit',
                         'dashboard:offer-restrictions'):
            response = self.get(reverse(url_name))
            self.assertEqual(302, response.status_code)

    def test_can_suspend_an_offer(self):
        # Create an offer
        offer = factories.create_offer()
        self.assertFalse(offer.is_suspended)

        detail_page = self.get(reverse('dashboard:offer-detail',
                                       kwargs={'pk': offer.pk}))
        form = detail_page.forms['status_form']
        form.submit('suspend')

        offer.refresh_from_db()
        self.assertTrue(offer.is_suspended)

    def test_can_reinstate_a_suspended_offer(self):
        # Create a suspended offer
        offer = factories.create_offer()
        offer.suspend()
        self.assertTrue(offer.is_suspended)

        detail_page = self.get(reverse('dashboard:offer-detail',
                                       kwargs={'pk': offer.pk}))
        form = detail_page.forms['status_form']
        form.submit('unsuspend')

        offer.refresh_from_db()
        self.assertFalse(offer.is_suspended)

    def test_can_change_offer_priority(self):
        offer = factories.create_offer()
        restrictions_page = self.get(reverse('dashboard:offer-restrictions', kwargs={'pk': offer.pk}))
        restrictions_page.form['priority'] = '12'
        restrictions_page.form.submit()
        offer.refresh_from_db()

        self.assertEqual(offer.priority, 12)

    def test_jump_back_to_incentive_step_for_new_offer(self):
        list_page = self.get(reverse('dashboard:offer-list'))

        metadata_page = list_page.click('Create new offer')
        metadata_form = metadata_page.form
        metadata_form['name'] = "Test offer"

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form
        benefit_form['range'] = self.range.id
        benefit_form['type'] = "Percentage"
        benefit_form['value'] = "25"

        benefit_form.submit()
        benefit_page = self.get(reverse('dashboard:offer-benefit'))
        # Accessing through context because WebTest form does not include an 'errors' field
        benefit_form = benefit_page.context['form']

        self.assertFalse('range' in benefit_form.errors)
        self.assertEqual(len(benefit_form.errors), 0)

    def test_jump_back_to_condition_step_for_new_offer(self):
        list_page = self.get(reverse('dashboard:offer-list'))

        metadata_page = list_page.click('Create new offer')
        metadata_form = metadata_page.form
        metadata_form['name'] = "Test offer"

        benefit_page = metadata_form.submit().follow()
        benefit_form = benefit_page.form
        benefit_form['range'] = self.range.id
        benefit_form['type'] = "Percentage"
        benefit_form['value'] = "25"

        condition_page = benefit_form.submit().follow()
        condition_form = condition_page.form
        condition_form['range'] = self.range.id
        condition_form['type'] = "Count"
        condition_form['value'] = "3"

        condition_form.submit()
        condition_page = self.get(reverse('dashboard:offer-condition'))

        self.assertFalse('range' in condition_page.errors)
        self.assertEqual(len(condition_page.errors), 0)

    def test_jump_to_incentive_step_for_existing_offer(self):
        offer = factories.create_offer()
        url = reverse('dashboard:offer-benefit', kwargs={'pk': offer.id})

        condition_page = self.get(url)

        self.assertFalse('range' in condition_page.errors)
        self.assertEqual(len(condition_page.errors), 0)

    def test_jump_to_condition_step_for_existing_offer(self):
        offer = factories.create_offer()
        url = reverse('dashboard:offer-condition', kwargs={'pk': offer.id})

        condition_page = self.get(url)

        self.assertFalse('range' in condition_page.errors)
        self.assertEqual(len(condition_page.errors), 0)
