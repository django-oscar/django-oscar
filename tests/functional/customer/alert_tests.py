import mock

from django_webtest import WebTest
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core import mail

from oscar.apps.customer.models import ProductAlert
from oscar.test.factories import create_product, create_stockrecord
from oscar.test.factories import UserFactory


class TestAUser(WebTest):

    def setUp(self):
        super(TestAUser, self).setUp()
        self.user = UserFactory()
        self.product = create_product(num_in_stock=0)

    def test_can_create_a_stock_alert(self):
        product_url = self.product.get_absolute_url()
        product_page = self.app.get(product_url, user=self.user)

        form = product_page.forms['alert_form']
        form.submit()

        alerts = ProductAlert.objects.filter(user=self.user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertEqual(ProductAlert.ACTIVE, alert.status)
        self.assertEqual(alert.product, self.product)

    def test_stock_alert_form_does_not_exist(self):
        with self.settings(OSCAR_HIDDEN_FEATURES=['alerts']):
            product_url = self.product.get_absolute_url()
            product_page = self.app.get(product_url, user=self.user)

        self.assertFalse('alert_form' in product_page.forms)


class TestAnAnonymousUser(WebTest):

    def setUp(self):
        super(TestAnAnonymousUser, self).setUp()
        self.product = create_product(num_in_stock=0)

    def test_can_create_a_stock_alert(self):
        product_page = self.app.get(self.product.get_absolute_url())
        form = product_page.forms['alert_form']
        form['email'] = 'john@smith.com'
        form.submit()

        alerts = ProductAlert.objects.filter(email='john@smith.com')
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertEqual(ProductAlert.UNCONFIRMED, alert.status)
        self.assertEqual(alert.product, self.product)

    def test_stock_alert_form_does_not_exist(self):
        with self.settings(OSCAR_HIDDEN_FEATURES=['alerts']):
            product_page = self.app.get(self.product.get_absolute_url())

        self.assertFalse('alert_form' in product_page.forms)


class TestAUserWithAnActiveStockAlert(WebTest):

    def setUp(self):
        self.user = UserFactory()
        self.product = create_product()
        self.stockrecord = create_stockrecord(self.product, num_in_stock=0)
        product_page = self.app.get(self.product.get_absolute_url(),
                                    user=self.user)
        form = product_page.forms['alert_form']
        form.submit()

    def test_can_cancel_it(self):
        alerts = ProductAlert.objects.filter(user=self.user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertFalse(alert.is_cancelled)
        self.app.get(reverse('customer:alerts-cancel-by-pk',
                             kwargs={'pk': alert.pk}),
                             user=self.user)

        alerts = ProductAlert.objects.filter(user=self.user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertTrue(alert.is_cancelled)

    def test_gets_notified_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        self.assertEqual(1, self.user.notifications.all().count())

    def test_gets_emailed_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        self.assertEqual(1, len(mail.outbox))

    def test_does_not_get_emailed_when_it_is_saved_but_still_zero_stock(self):
        self.stockrecord.num_in_stock = 0
        self.stockrecord.save()
        self.assertEqual(0, len(mail.outbox))


class TestProfilePage(WebTest):
    def test_alerts_link_exists(self):
        """
        Because of differences between src/oscar/templates/oscar/layout.html
        and tests/_site/templates/layout.html, this test will always fail.

        See https://github.com/django-oscar/django-oscar/issues/1991 for
        a complete explanation.

        Feel free to uncomment the body of this method when that issue has
        been resolved.
        """
#        account_page = self.app.get(reverse('customer:profile-view'))
#
#        html = account_page.content.decode('utf-8')
#        self.assertTrue(reverse('customer:alerts-list') in html)

    def test_alerts_link_does_not_exist(self):
        with self.settings(OSCAR_HIDDEN_FEATURES=['alerts']):
            account_page = self.app.get(reverse('customer:profile-view'))

        html = account_page.content.decode('utf-8')
        self.assertFalse(reverse('customer:alerts-list') in html)


class TestDashboard(WebTest):

    def setUp(self):
        super(TestDashboard, self).setUp()
        u = UserFactory()
        u.is_superuser = True
        u.is_staff = True
        u.save()

        self.user = u
        self.index_url = reverse('dashboard:index')

    def test_alerts_link_exists(self):
        dashboard_index = self.app.get(self.index_url, user=self.user)

        html = dashboard_index.content.decode('utf-8')
        self.assertTrue(reverse('dashboard:user-alert-list') in html)

    def test_alerts_link_does_not_exist(self):
        """
        oscar.apps.dashboard.nav.default_access_fn will omit a link from
        the dashboard navigation if the user isn't authorized to view it OR
        if Django fails to resolve the URL name.

        oscar.apps.dashboard.user.app will only register the user-alert URLs
        if the "alerts" feature is NOT hidden.

        Django registers URLs no later than the first call to self.app.get.
        Because tests.settings doesn't hide any apps, the user-alerts URLs
        will be reversible (and thus visible on the dashboard) regardless of
        whether or not we patch 'alerts' into OSCAR_HIDDEN_FEATURES at runtime.

        We can circumvent this limitation by using mock.patch to replace the
        reverse function so that it raises NoReverseMatch for user-alert URLs.

        It is unfortunate that this explanation is longer than the test.
        """

        def fake_reverse(url_identifier, *pos, **kw):
            app, name = url_identifier.split(':')
            if name.startswith('user-alert'):
                raise NoReverseMatch()
            return "/this/looks/like/a/valid/url"

        patch_target = 'oscar.apps.dashboard.nav.reverse'
        with mock.patch(patch_target, side_effect=fake_reverse):
            with self.settings(OSCAR_HIDDEN_FEATURES=['alerts']):
                dashboard_index = self.app.get(self.index_url, user=self.user)

        html = dashboard_index.content.decode('utf-8')
        self.assertFalse(reverse('dashboard:user-alert-list') in html)
