import re

from django.contrib.auth import models
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django_webtest import WebTest

from oscar_testsupport.testcases import WebTestCase


class TestAUserWhoseForgottenHerPassword(WebTest):

    def test_can_reset_her_password(self):
        username, email, password = 'lucy', 'lucy@example.com', 'password'
        models.User.objects.create_user(
            username, email, password)

        # Fill in password reset form
        page = self.app.get(reverse('password-reset'))
        form = page.forms['password_reset_form']
        form['email'] = email
        response = form.submit()

        # Response should be a redirect and an email should have been sent
        self.assertEqual(302, response.status_code)
        self.assertEqual(1, len(mail.outbox))

        # Extract URL from email
        email_body = mail.outbox[0].body
        urlfinder = re.compile(r"http://example.com(?P<path>[-A-Za-z0-9\/\._]+)")
        matches = urlfinder.search(email_body, re.MULTILINE)
        self.assertTrue('path' in matches.groupdict())
        path = matches.groupdict()['path']

        # Reset password and check we get redirect
        reset_page = self.app.get(path)
        form = reset_page.forms['password_reset_form']
        form['new_password1'] = 'monkey'
        form['new_password2'] = 'monkey'
        response = form.submit()
        self.assertEqual(302, response.status_code)

        # Now attempt to login with new password
        url = reverse('customer:login')
        form = self.app.get(url).forms['login_form']
        form['login-username'] = email
        form['login-password'] = 'monkey'
        response = form.submit('login_submit')
        self.assertEqual(302, response.status_code)


class TestAnAnonymousUser(WebTestCase):

    def test_can_login(self):
        email, password = 'd@d.com', 'mypassword'
        User.objects.create_user('_', email, password)

        url = reverse('customer:login')
        form = self.app.get(url).forms['login_form']
        form['login-username'] = email
        form['login-password'] = password
        response = form.submit('login_submit')
        self.assertRedirectsTo(response, 'customer:summary')

    def test_can_register(self):
        url = reverse('customer:register')
        form = self.app.get(url).forms['register_form']
        form['registration-email'] = 'terry@boom.com'
        form['registration-password1'] = 'hedgehog'
        form['registration-password2'] = 'hedgehog'
        response = form.submit()
        self.assertRedirectsTo(response, 'customer:summary')
