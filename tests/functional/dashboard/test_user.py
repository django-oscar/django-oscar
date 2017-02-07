from django.core.urlresolvers import reverse
from django.core import mail
from django.utils.translation import ugettext_lazy as _
from webtest import AppError

from oscar.core.compat import get_user_model
from oscar.test.factories import UserFactory
from oscar.test.testcases import WebTestCase

User = get_user_model()


class IndexViewTests(WebTestCase):
    is_staff = True
    active_users_ids = []
    inactive_users_ids = []

    csrf_checks = False

    def setUp(self):
        super(IndexViewTests, self).setUp()
        for i in range(1, 25):
            UserFactory(is_active=True)
        for i in range(1, 25):
            UserFactory(is_active=False)

        user_queryset = User.objects.all()
        self.active_users_ids = user_queryset.filter(is_active=True).values_list('id', flat=True)
        self.inactive_users_ids = user_queryset.filter(is_active=False).values_list('id', flat=True)

    def test_user_list_view(self):
        response = self.get(reverse('dashboard:users-index'))
        self.assertInContext(response, 'users')

    def test_make_active(self):
        params = {'action': 'make_active',
                  'selected_user': self.inactive_users_ids}
        response = self.post(reverse('dashboard:users-index'), params=params)
        ex_inactive = User.objects.get(id=self.inactive_users_ids[10])
        self.assertIsRedirect(response)
        self.assertTrue(ex_inactive.is_active)

    def test_make_inactive(self):
        params = {'action': 'make_inactive',
                  'selected_user': self.active_users_ids}
        response = self.post(reverse('dashboard:users-index'), params=params)
        ex_active = User.objects.get(id=self.active_users_ids[10])
        self.assertIsRedirect(response)
        self.assertFalse(ex_active.is_active)


class DetailViewTests(WebTestCase):
    is_staff = True

    def test_user_detail_view(self):
        response = self.get(
            reverse('dashboard:user-detail', kwargs={'pk': self.user.pk}))
        self.assertInContext(response, 'user')
        self.assertIsOk(response)


class TestDetailViewForStaffUser(WebTestCase):
    is_staff = True

    def setUp(self):
        self.customer = UserFactory(
            username='jane', email='jane@example.org', password='password')
        super(TestDetailViewForStaffUser, self).setUp()

    def test_password_reset_url_only_available_via_post(self):
        try:
            reset_url = reverse(
                'dashboard:user-password-reset',
                kwargs={'pk': self.customer.id}
            )
            self.get(reset_url)
        except AppError as e:
            self.assertIn('405', e.args[0])

    def test_admin_can_reset_user_passwords(self):
        customer_page_url = reverse(
            'dashboard:user-detail',
            kwargs={'pk': self.customer.id}
        )
        customer_page = self.get(customer_page_url)
        reset_form = customer_page.forms['password_reset_form']
        response = reset_form.submit()

        # Check that the staff user is redirected back to the customer page
        self.assertRedirects(response, customer_page_url)

        # Check that the reset email has been sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Resetting your password", mail.outbox[0].subject)

        # Check that success message shows up
        self.assertContains(
            response.follow(),
            _("A password reset email has been sent")
        )
