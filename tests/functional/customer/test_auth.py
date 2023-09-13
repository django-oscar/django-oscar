import re

from django.core import mail
from django.urls import reverse
from django_webtest import WebTest

from oscar.core.compat import get_user_model
from oscar.test import factories
from oscar.test.testcases import WebTestCase

User = get_user_model()


class TestAUserWhoseForgottenHerPassword(WebTest):
    def test_can_reset_her_password(self):
        username, email, password = "lucy", "lucy@example.com", "password"
        User.objects.create_user(username, email, password)

        # Fill in password reset form
        page = self.app.get(reverse("password-reset"))
        form = page.forms["password_reset_form"]
        form["email"] = email
        response = form.submit()

        # Response should be a redirect and an email should have been sent
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, len(mail.outbox))

        # Extract URL from email
        email_body = mail.outbox[0].body
        urlfinder = re.compile(r"http://example.com(?P<path>[-A-Za-z0-9\/\._]+)")
        matches = urlfinder.search(email_body, re.MULTILINE)
        self.assertTrue("path" in matches.groupdict())
        path = matches.groupdict()["path"]

        # Reset password and check we get redirected
        reset_page_redirect = self.app.get(path)
        # The link in the email will redirect us to the password reset view
        reset_page = self.app.get(reset_page_redirect.location)
        form = reset_page.forms["password_reset_form"]
        form["new_password1"] = "crazymonkey"
        form["new_password2"] = "crazymonkey"
        response = form.submit()
        self.assertEqual(302, response.status_code)

        # Now attempt to login with new password
        url = reverse("customer:login")
        form = self.app.get(url).forms["login_form"]
        form["login-username"] = email
        form["login-password"] = "crazymonkey"
        response = form.submit("login_submit")
        self.assertEqual(302, response.status_code)


class TestAnAuthenticatedUser(WebTestCase):
    is_anonymous = False

    def test_receives_an_email_when_their_password_is_changed(self):
        page = self.get(reverse("customer:change-password"))
        form = page.forms["change_password_form"]
        form["old_password"] = self.password
        form["new_password1"] = "anotherfancypassword"
        form["new_password2"] = "anotherfancypassword"
        page = form.submit()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("your password has been changed", mail.outbox[0].body)

    def test_cannot_access_reset_password_page(self):
        response = self.get(reverse("password-reset"), status=403)
        self.assertEqual(403, response.status_code)

    def test_does_not_receive_an_email_when_their_profile_is_updated_but_email_address_not_changed(
        self,
    ):
        page = self.get(reverse("customer:profile-update"))
        form = page.forms["profile_form"]
        form["first_name"] = "Terry"
        form.submit()
        self.assertEqual(len(mail.outbox), 0)

    def test_receives_an_email_when_their_email_address_is_changed(self):
        page = self.get(reverse("customer:profile-update"))
        form = page.forms["profile_form"]

        new_email = "a.new.email@user.com"
        form["email"] = new_email
        page = form.submit()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.email)
        self.assertEqual(User.objects.get(id=self.user.id).email, new_email)
        self.assertIn("your email address has been changed", mail.outbox[0].body)


class TestAnAnonymousUser(WebTestCase):
    is_anonymous = True

    def assertCanLogin(self, email, password):
        url = reverse("customer:login")
        form = self.app.get(url).forms["login_form"]
        form["login-username"] = email
        form["login-password"] = password
        response = form.submit("login_submit")
        self.assertRedirectsTo(response, "customer:summary")

    def test_can_login(self):
        email, password = "d@d.com", "mypassword"
        User.objects.create_user("_", email, password)
        self.assertCanLogin(email, password)

    def test_can_login_with_email_containing_capitals_in_local_part(self):
        email, password = "Andrew.Smith@test.com", "mypassword"
        User.objects.create_user("_", email, password)
        self.assertCanLogin(email, password)

    def test_can_login_with_email_containing_capitals_in_host(self):
        email, password = "Andrew.Smith@teSt.com", "mypassword"
        User.objects.create_user("_", email, password)
        self.assertCanLogin(email, password)

    def test_can_register(self):
        url = reverse("customer:register")
        form = self.app.get(url).forms["register_form"]
        form["email"] = "terry@boom.com"
        form["password1"] = form["password2"] = "hedgehog"
        response = form.submit()
        self.assertRedirectsTo(response, "customer:summary")

    def test_casing_of_local_part_of_email_is_preserved(self):
        url = reverse("customer:register")
        form = self.app.get(url).forms["register_form"]
        form["email"] = "Terry@Boom.com"
        form["password1"] = form["password2"] = "hedgehog"
        form.submit()
        user = User.objects.all()[0]
        self.assertEqual(user.email, "Terry@boom.com")


class TestAStaffUser(WebTestCase):
    is_anonymous = True
    password = "testing"

    def setUp(self):
        self.staff = factories.UserFactory.create(password=self.password, is_staff=True)
        super().setUp()

    def test_gets_redirected_to_the_dashboard_when_they_login(self):
        page = self.get(reverse("customer:login"))
        form = page.forms["login_form"]
        form["login-username"] = self.staff.email
        form["login-password"] = self.password
        response = form.submit("login_submit")

        self.assertRedirectsTo(response, "dashboard:index")
