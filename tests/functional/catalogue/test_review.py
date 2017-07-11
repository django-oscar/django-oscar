from oscar.test.testcases import WebTestCase
from oscar.test.factories import create_product, UserFactory
from oscar.apps.catalogue.reviews.signals import review_added
from oscar.test.contextmanagers import mock_signal_receiver


class TestACustomer(WebTestCase):

    def setUp(self):
        self.product = create_product()

    def test_can_add_a_review_when_anonymous(self):
        detail_page = self.app.get(self.product.get_absolute_url())
        add_review_page = detail_page.click(linkid='write_review')
        form = add_review_page.forms['add_review_form']
        form['title'] = 'This is great!'
        form['score'] = 5
        form['body'] = 'Loving it, loving it, loving it'
        form['name'] = 'John Doe'
        form['email'] = 'john@example.com'
        form.submit()

        self.assertEqual(1, self.product.reviews.all().count())

    def test_can_add_a_review_when_signed_in(self):
        user = UserFactory()
        detail_page = self.app.get(self.product.get_absolute_url(),
                                   user=user)
        add_review_page = detail_page.click(linkid="write_review")
        form = add_review_page.forms['add_review_form']
        form['title'] = 'This is great!'
        form['score'] = 5
        form['body'] = 'Loving it, loving it, loving it'
        form.submit()

        self.assertEqual(1, self.product.reviews.all().count())

    def test_adding_a_review_sends_a_signal(self):
        review_user = UserFactory()
        detail_page = self.app.get(self.product.get_absolute_url(),
                                   user=review_user)
        with mock_signal_receiver(review_added) as receiver:
            add_review_page = detail_page.click(linkid="write_review")
            form = add_review_page.forms['add_review_form']
            form['title'] = 'This is great!'
            form['score'] = 5
            form['body'] = 'Loving it, loving it, loving it'
            form.submit()
            self.assertEqual(receiver.call_count, 1)
        self.assertEqual(1, self.product.reviews.all().count())
