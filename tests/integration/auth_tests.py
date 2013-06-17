from django.test import TestCase
from django.contrib.auth import authenticate
from django.core import mail

from oscar.core.compat import get_user_model

User = get_user_model()


class TestEmailAuthBackendWhenUsersShareAnEmail(TestCase):

    def test_authenticates_when_passwords_are_different(self):
        # Create two users with the same email address
        email = 'person@example.com'
        for username in ['user1', 'user2']:
            User.objects.create_user(username, email, password=username)

        user = authenticate(username=email, password='user1')
        self.assertTrue(user is not None)

    def test_rejects_when_passwords_match(self):
        # Create two users with the same email address
        email = 'person@example.com'
        for username in ['user1', 'user2']:
            User.objects.create_user(username, email, password='password')

        user = authenticate(username=email, password='password')
        self.assertTrue(user is None)

    def test_mails_admins_when_passwords_match(self):
        # Create two users with the same email address
        email = 'person@example.com'
        for username in ['user1', 'user2']:
            User.objects.create_user(username, email, password='password')

        authenticate(username=email, password='password')
        self.assertEqual(1, len(mail.outbox))
