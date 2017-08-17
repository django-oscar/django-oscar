from django.contrib.sessions.middleware import SessionMiddleware
from mock import Mock

from oscar.apps.checkout.forms import ShippingAddressForm
from oscar.apps.checkout.utils import CheckoutSessionData


def add_session_to_request(request):
    """Annotate a request object with a session"""
    middleware = SessionMiddleware()
    middleware.process_request(request)


def get_address_fields():
    def new_init(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)

    ShippingAddressForm.__init__ = new_init

    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'line1': '1 Egg Road',
        'line4': 'Shell City',
        'postcode': 'N12 9RT',
        'phone_number': '+49231555555',
    }

    form = ShippingAddressForm(data)
    form.is_valid()
    form.clean()
    address_fields = dict(
        (k, v) for (k, v) in form.instance.__dict__.items()
        if not k.startswith('_'))
    return address_fields


def test_checkout_session_data_creation(rf):
    request = rf.get('/')
    add_session_to_request(request)
    CheckoutSessionData(request)


def test_set_get_guest_email(rf):
    request = rf.get('/')
    add_session_to_request(request)
    session = CheckoutSessionData(request)
    email = 'info@example.com'
    session.set_guest_email(email)
    assert session.request.session[session.SESSION_KEY]['guest']['email'] == email
    assert session.get_guest_email() == email


def test_reset_shipping_data(rf):
    request = rf.get('/')
    add_session_to_request(request)
    session = CheckoutSessionData(request)
    session.reset_shipping_data()
    assert session.request.session[session.SESSION_KEY]['shipping'] == {}


def test_ship_to_user_address(rf):
    request = rf.get('/')
    add_session_to_request(request)
    session = CheckoutSessionData(request)
    address = Mock(id=1)
    session.ship_to_user_address(address)
    assert session.request.session[session.SESSION_KEY]['shipping']['user_address_id'] == 1
    assert session.shipping_user_address_id() == 1


def test_serialize_new_address_with_phone_number(rf):
    address_fields = get_address_fields()
    request = rf.get('/')
    add_session_to_request(request)
    session = CheckoutSessionData(request)

    session.ship_to_new_address(address_fields)
    session.bill_to_new_address(address_fields)
    data = session.request.session._get_session(no_load=True)
    assert session.request.session.encode(data)
