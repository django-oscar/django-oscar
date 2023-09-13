# pylint: disable=redefined-outer-name
from unittest.mock import Mock

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse

from oscar.apps.checkout.forms import ShippingAddressForm
from oscar.apps.checkout.utils import CheckoutSessionData


def get_response_for_test(request):
    return HttpResponse()


@pytest.fixture
def csdf(rf):
    """"""
    request = rf.get("/")
    middleware = SessionMiddleware(get_response_for_test)
    middleware.process_request(request)
    return CheckoutSessionData(request)


def get_address_fields():
    def new_init(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)

    ShippingAddressForm.__init__ = new_init

    data = {
        "first_name": "John",
        "last_name": "Doe",
        "line1": "1 Egg Road",
        "line4": "Shell City",
        "postcode": "N12 9RT",
        "phone_number": "+49231555555",
    }

    form = ShippingAddressForm(data)
    form.is_valid()
    address_fields = dict(
        (k, v) for (k, v) in form.instance.__dict__.items() if not k.startswith("_")
    )
    return address_fields


def test__get(csdf):
    value = csdf._get("non-existent-namespace", "non-existent-key", "default-value")
    assert value == "default-value"


def test__unset(csdf):
    csdf._set("test-namespace", "test-key", "test-value")
    csdf._unset("test-namespace", "test-key")
    assert "test-key" not in csdf.request.session[csdf.SESSION_KEY]["test-namespace"]


def test_flush(csdf):
    csdf._set("test-namespace", "the-key", "the-value")
    csdf.flush()
    assert csdf.request.session[csdf.SESSION_KEY] == {}


def test_set_get_guest_email(csdf):
    email = "info@example.com"
    csdf.set_guest_email(email)
    assert csdf.request.session[csdf.SESSION_KEY]["guest"]["email"] == email
    assert csdf.get_guest_email() == email


def test_reset_shipping_data(csdf):
    csdf.reset_shipping_data()
    assert csdf.request.session[csdf.SESSION_KEY]["shipping"] == {}


def test_ship_to_user_address(csdf):
    address = Mock(id=1)
    csdf.ship_to_user_address(address)
    assert csdf.request.session[csdf.SESSION_KEY]["shipping"]["user_address_id"] == 1
    assert csdf.shipping_user_address_id() == 1


def test_serialize_new_address_with_phone_number(csdf):
    address_fields = get_address_fields()
    csdf.ship_to_new_address(address_fields)
    csdf.bill_to_new_address(address_fields)
    data = csdf.request.session._get_session(no_load=True)
    assert csdf.request.session.encode(data)
    address_fields["phone_number"] = address_fields["phone_number"].as_international
    assert (
        address_fields
        == csdf.new_billing_address_fields()
        == csdf.new_shipping_address_fields()
    )


def test_new_shipping_address_fields(csdf):
    address_fields = get_address_fields()
    csdf.ship_to_new_address(address_fields)
    address_fields["phone_number"] = address_fields["phone_number"].as_international
    assert address_fields == csdf.new_shipping_address_fields()


def test_use_free_shipping(csdf):
    csdf.use_free_shipping()
    assert (
        csdf.request.session[csdf.SESSION_KEY]["shipping"]["method_code"] == "__free__"
    )


def test_bill_to_shipping_address(csdf):
    address = Mock(id=1)
    csdf.bill_to_user_address(address)
    assert csdf.billing_user_address_id() == 1
    csdf.bill_to_shipping_address()
    assert "user_address_id" not in csdf.request.session[csdf.SESSION_KEY]["billing"]
    assert (
        csdf.request.session[csdf.SESSION_KEY]["billing"][
            "billing_address_same_as_shipping"
        ]
        is True
    )
    assert csdf.is_billing_address_same_as_shipping() is True
    assert csdf.is_billing_address_set() is True


def test_payment_methods(csdf):
    csdf.pay_by("paypal")
    assert csdf.request.session[csdf.SESSION_KEY]["payment"]["method"] == "paypal"
    assert csdf.payment_method() == "paypal"


def test_order_number(csdf):
    """
    :param CheckoutSessionData csdf:
    :return:
    """
    csdf.set_order_number("55555")
    assert csdf.get_order_number() == "55555"
