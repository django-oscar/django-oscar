from django_webtest import WebTest
from django.core.urlresolvers import reverse
from django.core import mail
from django_dynamic_fixture import G

from oscar_testsupport.factories import create_product
from oscar.core.compat import get_user_model
from oscar.apps.customer.models import ProductAlert


User = get_user_model()

class TestAUser(WebTest):

    def test_can_create_a_stock_alert(self):
        user = G(User)
        product = create_product(num_in_stock=0)
        product_page = self.app.get(product.get_absolute_url(), user=user)
        form = product_page.forms['alert_form']
        form.submit()

        alerts = ProductAlert.objects.filter(user=user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertEqual(ProductAlert.ACTIVE, alert.status)
        self.assertEqual(alert.product, product)


class TestAUserWithAnActiveStockAlert(WebTest):

    def setUp(self):
        self.user = G(User)
        self.product = create_product(num_in_stock=0)
        product_page = self.app.get(self.product.get_absolute_url(),
                                    user=self.user)
        form = product_page.forms['alert_form']
        form.submit()

    def test_can_cancel_it(self):
        account_page = self.app.get(reverse('customer:summary'),
                                    user=self.user)
        form = account_page.forms['alerts_form']
        form.submit('cancel_alert')

        alerts = ProductAlert.objects.filter(user=self.user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertTrue(alert.is_cancelled)

    def test_gets_notified_when_it_is_back_in_stock(self):
        self.product.stockrecord.num_in_stock = 10
        self.product.stockrecord.save()
        self.assertEqual(1, self.user.notifications.all().count())

    def test_gets_emailed_when_it_is_back_in_stock(self):
        self.product.stockrecord.num_in_stock = 10
        self.product.stockrecord.save()
        self.assertEqual(1, len(mail.outbox))

    def test_does_not_get_emailed_when_it_is_saved_but_still_zero_stock(self):
        self.product.stockrecord.num_in_stock = 0
        self.product.stockrecord.save()
        self.assertEqual(0, len(mail.outbox))


class TestAnAnonymousUser(WebTest):

    def test_can_create_a_stock_alert(self):
        product = create_product(num_in_stock=0)
        product_page = self.app.get(product.get_absolute_url())
        form = product_page.forms['alert_form']
        form['email'] = 'john@smith.com'
        form.submit()

        alerts = ProductAlert.objects.filter(email='john@smith.com')
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertEqual(ProductAlert.UNCONFIRMED, alert.status)
        self.assertEqual(alert.product, product)
