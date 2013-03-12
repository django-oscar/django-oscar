from django_dynamic_fixture import G
from django.contrib.auth.models import User

from mock import Mock
import contextlib

from oscar_testsupport.testcases import WebTestCase
from oscar_testsupport.factories import create_product

from oscar.apps.catalogue.reviews.signals import review_added


@contextlib.contextmanager
def mock_signal_receiver(signal, wraps=None, **kwargs):
    """
    Temporarily attaches a receiver to the provided ``signal`` within the scope
    of the context manager.

    >>> with mock_signal_receiver(post_save, sender=Model) as receiver:
    >>> Model.objects.create()
    >>> assert receiver.call_count = 1
    """
    if wraps is None:
        wraps = lambda *args, **kwargs: None

    receiver = Mock(wraps=wraps)
    signal.connect(receiver, **kwargs)
    yield receiver
    signal.disconnect(receiver)


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

    def test_adding_a_review_sends_a_signal(self):
        review_user = G(User)
        detail_page = self.app.get(self.product.get_absolute_url(),
                                   user=review_user)
        with mock_signal_receiver(review_added) as receiver:
            add_review_page = detail_page.click(linkid="write_review")
            form = add_review_page.forms['add_review_form']
            form['title'] = 'This is great!'
            form['score'] = 5
            form['body'] = 'Loving it, loving it, loving it'
            form.submit()
            self.assertEquals(receiver.call_count, 1)
        self.assertEqual(1, self.product.reviews.all().count())
