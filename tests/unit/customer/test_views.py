from unittest.mock import Mock, patch

from django.test import Client, TestCase
from django.urls import reverse

from oscar.apps.customer.forms import EmailAuthenticationForm


class TestAccountAuthView(TestCase):
    def setUp(self):
        self.client = Client()

    def test_request_is_passed_to_form(self):
        form_class = Mock(wraps=EmailAuthenticationForm)
        data = {"login_submit": ["1"]}
        initial = {"redirect_url": ""}
        with patch(
            "oscar.apps.customer.views.AccountAuthView.login_form_class", new=form_class
        ):
            response = self.client.post(reverse("customer:login"), data=data)
            assert form_class.called
            form_class.assert_called_with(
                data=data,
                files={},
                host="testserver",
                initial=initial,
                prefix="login",
                request=response.wsgi_request,
            )
