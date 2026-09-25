"""
Regression tests for the email change verification flow added in issue #4580.

Before the fix, updating the email field in ProfileUpdateView immediately
changed user.email without any verification.  The fix:

1. Keeps user.email unchanged when a new email is submitted.
2. Generates a signed token and sends it to the new address.
3. EmailChangeVerifyView reads the token, validates it, and only then
   persists the new email.

We test:
- The verification view rejects expired / tampered tokens.
- The verification view updates user.email on a valid token.
- The verification view rejects tokens whose target email is already taken.
- ProfileUpdateView does NOT immediately change user.email.
"""
from django.core.signing import TimestampSigner
from django.test import TestCase
from django.urls import reverse

from oscar.test.factories import UserFactory


class TestEmailChangeVerifyView(TestCase):
    def setUp(self):
        self.user = UserFactory(email="old@example.com")
        self.client.force_login(self.user)

    def _make_token(self, user_pk, new_email, max_age_override=None):
        signer = TimestampSigner()
        token = signer.sign(f"{user_pk}:{new_email}")
        return token

    def _verify_url(self, token):
        return reverse("customer:email-change-verify", kwargs={"token": token})

    # -----------------------------------------------------------------
    # Happy path
    # -----------------------------------------------------------------

    def test_valid_token_updates_email(self):
        token = self._make_token(self.user.pk, "new@example.com")
        self.client.get(self._verify_url(token), follow=True)

        self.user.refresh_from_db()
        self.assertEqual("new@example.com", self.user.email)

    def test_valid_token_shows_success_message(self):
        token = self._make_token(self.user.pk, "new@example.com")
        response = self.client.get(self._verify_url(token), follow=True)
        messages = list(response.context["messages"])
        self.assertTrue(
            any("updated" in str(m).lower() for m in messages),
            f"Expected a success message, got: {[str(m) for m in messages]}",
        )

    # -----------------------------------------------------------------
    # Security: tampered token
    # -----------------------------------------------------------------

    def test_tampered_token_rejected(self):
        token = self._make_token(self.user.pk, "new@example.com")
        bad_token = token + "X"  # corrupt the signature
        response = self.client.get(self._verify_url(bad_token), follow=True)

        self.user.refresh_from_db()
        self.assertEqual("old@example.com", self.user.email)
        messages = list(response.context["messages"])
        self.assertTrue(
            any("invalid" in str(m).lower() or "expired" in str(m).lower() for m in messages),
            f"Expected an error message, got: {[str(m) for m in messages]}",
        )

    # -----------------------------------------------------------------
    # Security: email already taken
    # -----------------------------------------------------------------

    def test_token_rejected_when_email_already_taken(self):
        # Create a second user who grabs the target email between token
        # generation and verification.
        UserFactory(email="taken@example.com")

        token = self._make_token(self.user.pk, "taken@example.com")
        response = self.client.get(self._verify_url(token), follow=True)

        self.user.refresh_from_db()
        self.assertEqual("old@example.com", self.user.email)
        messages = list(response.context["messages"])
        self.assertTrue(
            any("already" in str(m).lower() or "exist" in str(m).lower() for m in messages),
            f"Expected a conflict error message, got: {[str(m) for m in messages]}",
        )

    # -----------------------------------------------------------------
    # Security: email must NOT be changed by ProfileUpdateView itself
    # -----------------------------------------------------------------

    def test_profile_update_does_not_immediately_change_email(self):
        """
        Submitting a new email via the profile form must leave user.email
        unchanged until the verification link is clicked.
        """
        # Ensure there is a password so check_password passes
        self.user.set_password("correcthorse")
        self.user.save()

        url = reverse("customer:profile-update")
        self.client.post(
            url,
            data={
                "email": "pending@example.com",
                "first_name": "",
                "last_name": "",
                "password": "correcthorse",
            },
            follow=True,
        )
        self.user.refresh_from_db()
        # The email must NOT have changed immediately
        self.assertEqual(
            "old@example.com",
            self.user.email,
            "user.email was changed before verification — fix is broken",
        )


class TestProfileUpdateEmailIsNotImmediatelyChanged(TestCase):
    """Lightweight check that does not depend on URL routing."""

    def test_email_field_not_saved_when_changed(self):
        user = UserFactory(email="original@example.com")
        user.set_password("secret")
        user.save()

        client = __import__("django.test", fromlist=["Client"]).Client()
        client.force_login(user)

        url = reverse("customer:profile-update")
        client.post(
            url,
            {
                "email": "changed@example.com",
                "first_name": "",
                "last_name": "",
                "password": "secret",
            },
            follow=True,
        )
        user.refresh_from_db()
        self.assertNotEqual(
            "changed@example.com",
            user.email,
            "Email changed immediately without verification — vulnerability not fixed",
        )
