from django.core import mail
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from webtest import AppError

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.test.factories import ProductAlertFactory, UserFactory
from oscar.test.testcases import WebTestCase

User = get_user_model()
ProductAlert = get_model("customer", "ProductAlert")


class IndexViewTests(WebTestCase):
    is_staff = True
    active_users_ids = []
    inactive_users_ids = []

    csrf_checks = False

    def setUp(self):
        super().setUp()
        for _ in range(1, 25):
            UserFactory(is_active=True)
        for _ in range(1, 25):
            UserFactory(is_active=False)

        user_queryset = User.objects.all()
        self.active_users_ids = user_queryset.filter(is_active=True).values_list(
            "id", flat=True
        )
        self.inactive_users_ids = user_queryset.filter(is_active=False).values_list(
            "id", flat=True
        )

    def test_user_list_view(self):
        response = self.get(reverse("dashboard:users-index"))
        self.assertInContext(response, "users")

    def test_make_active(self):
        params = {"action": "make_active", "selected_user": self.inactive_users_ids}
        response = self.post(reverse("dashboard:users-index"), params=params)
        ex_inactive = User.objects.get(id=self.inactive_users_ids[10])
        self.assertIsRedirect(response)
        self.assertTrue(ex_inactive.is_active)

    def test_make_inactive(self):
        params = {"action": "make_inactive", "selected_user": self.active_users_ids}
        response = self.post(reverse("dashboard:users-index"), params=params)
        ex_active = User.objects.get(id=self.active_users_ids[10])
        self.assertIsRedirect(response)
        self.assertFalse(ex_active.is_active)


class DetailViewTests(WebTestCase):
    is_staff = True

    def test_user_detail_view(self):
        response = self.get(
            reverse("dashboard:user-detail", kwargs={"pk": self.user.pk})
        )
        self.assertInContext(response, "user")
        self.assertIsOk(response)


class TestDetailViewForStaffUser(WebTestCase):
    is_staff = True

    def setUp(self):
        self.customer = UserFactory(
            username="jane", email="jane@example.org", password="password"
        )
        super().setUp()

    def test_password_reset_url_only_available_via_post(self):
        try:
            reset_url = reverse(
                "dashboard:user-password-reset", kwargs={"pk": self.customer.id}
            )
            self.get(reset_url)
        except AppError as e:
            self.assertIn("405", e.args[0])

    def test_admin_can_reset_user_passwords(self):
        customer_page_url = reverse(
            "dashboard:user-detail", kwargs={"pk": self.customer.id}
        )
        customer_page = self.get(customer_page_url)
        reset_form = customer_page.forms["password_reset_form"]
        response = reset_form.submit()

        # Check that the staff user is redirected back to the customer page
        self.assertRedirects(response, customer_page_url)

        # Check that the reset email has been sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Resetting your password", mail.outbox[0].subject)

        # Check that success message shows up
        self.assertContains(
            response.follow(), _("A password reset email has been sent")
        )


class SearchTests(WebTestCase):
    is_staff = True
    url = reverse_lazy("dashboard:users-index")

    def setUp(self):
        UserFactory(
            username="lars",
            email="lars@example.org",
            first_name="Lars",
            last_name="van der Berg",
        )
        UserFactory(
            username="owen",
            email="owen@example.org",
            first_name="Owen",
            last_name="Davies",
        )
        UserFactory(
            username="robalan",
            email="robalan@example.org",
            first_name="Rob Alan",
            last_name="Lewis",
        )
        super().setUp()

    def _search_by_form_args(self, form_args):
        response = self.get(self.url)
        search_form = response.forms[0]
        for field_name, val in form_args.items():
            search_form[field_name] = val
        search_response = search_form.submit("search")
        data = search_response.context["users"].data
        return data

    def test_user_name_2_parts(self):
        data = self._search_by_form_args({"name": "Owen Davies"})
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].email, "owen@example.org")
        self.assertEqual(data[0].first_name, "Owen")
        self.assertEqual(data[0].last_name, "Davies")

    def test_user_name_3_parts(self):
        data = self._search_by_form_args({"name": "Rob Alan Lewis"})
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].email, "robalan@example.org")
        self.assertEqual(data[0].first_name, "Rob Alan")
        self.assertEqual(data[0].last_name, "Lewis")

    def test_user_name_4_parts(self):
        data = self._search_by_form_args({"name": "Lars van der Berg"})
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].email, "lars@example.org")
        self.assertEqual(data[0].first_name, "Lars")
        self.assertEqual(data[0].last_name, "van der Berg")


class ProductAlertListViewTestCase(WebTestCase):
    is_staff = True

    def test_list_view_get_queryset_ordering(self):
        ProductAlertFactory.create_batch(3)
        response = self.get(reverse("dashboard:user-alert-list"))
        self.assertEqual(
            list(response.context["alerts"]),
            list(ProductAlert.objects.order_by("-date_created")),
        )

    def test_list_view_status_filtering(self):
        ProductAlertFactory.create_batch(3, status=ProductAlert.CANCELLED)
        ProductAlertFactory.create_batch(2, status=ProductAlert.ACTIVE)

        response = self.get(
            reverse("dashboard:user-alert-list"), params={"status": ProductAlert.ACTIVE}
        )
        self.assertEqual(len(response.context["alerts"]), 2)
