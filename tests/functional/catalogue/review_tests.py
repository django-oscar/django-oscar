from django_dynamic_fixture import G
from django.contrib.auth.models import User

from oscar_testsupport.testcases import WebTestCase
from oscar_testsupport.factories import create_product


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
        user = G(User)
        detail_page = self.app.get(self.product.get_absolute_url(),
                                   user=user)
        add_review_page = detail_page.click(linkid="write_review")
        form = add_review_page.forms['add_review_form']
        form['title'] = 'This is great!'
        form['score'] = 5
        form['body'] = 'Loving it, loving it, loving it'
        form.submit()

        self.assertEqual(1, self.product.reviews.all().count())
