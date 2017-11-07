import unittest

import django
from django.test import TestCase

from oscar.apps.customer.auth_backends import EmailBackend
from oscar.test.factories import UserFactory


class AuthBackendTestCase(TestCase):

    def setUp(self):
        self.user = UserFactory(email='foo@example.com', is_staff=True)
        self.user.set_password('letmein')
        self.user.save()
        self.backend = EmailBackend()

    @unittest.skipUnless(django.VERSION < (1, 11), "for Django <1.11 only")
    def test_authentication_method_signature_pre_django_1_11(self):
        auth_result = self.backend.authenticate('foo@example.com', 'letmein')
        self.assertEqual(auth_result, self.user)

    @unittest.skipUnless(django.VERSION >= (1, 11), "for Django >=1.11 only")
    def test_authentication_method_signature_post_django_1_11(self):
        auth_result = self.backend.authenticate(None, 'foo@example.com', 'letmein')
        self.assertEqual(auth_result, self.user)

    def test_inactive_users_cannot_authenticate(self):
        self.user.is_active = False
        self.user.save()

        auth_result = self.backend.authenticate(None, 'foo@example.com', 'letmein')
        self.assertIsNone(auth_result)
