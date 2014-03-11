import warnings

from django.utils.encoding import force_text

from oscar.core.loading import get_class

Repository = get_class('shipping.repository', 'Repository')


class CheckoutSessionData(object):
    """
    Class responsible for marshalling all the checkout session data
    """
    SESSION_KEY = 'checkout_data'

    def __init__(self, request):
        self.request = request
        if self.SESSION_KEY not in self.request.session:
            self.request.session[self.SESSION_KEY] = {}

    def _check_namespace(self, namespace):
        if namespace not in self.request.session[self.SESSION_KEY]:
            self.request.session[self.SESSION_KEY][namespace] = {}

    def _get(self, namespace, key, default=None):
        """
        Return session value or None
        """
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            return self.request.session[self.SESSION_KEY][namespace][key]
        return default

    def _set(self, namespace, key, value):
        """
        Set session value
        """
        self._check_namespace(namespace)
        self.request.session[self.SESSION_KEY][namespace][key] = value
        self.request.session.modified = True

    def _unset(self, namespace, key):
        """
        Unset session value
        """
        self._check_namespace(namespace)
        if key in self.request.session[self.SESSION_KEY][namespace]:
            del self.request.session[self.SESSION_KEY][namespace][key]
            self.request.session.modified = True

    def _flush_namespace(self, namespace):
        self.request.session[self.SESSION_KEY][namespace] = {}
        self.request.session.modified = True

    def flush(self):
        """
        Delete session key
        """
        self.request.session[self.SESSION_KEY] = {}

    # Guest checkout

    def set_guest_email(self, email):
        self._set('guest', 'email', email)

    def get_guest_email(self):
        return self._get('guest', 'email')

    # Shipping address
    # ================
    # Options:
    # 1. No shipping required (eg digital products)
    # 2. Ship to new address (entered in a form)
    # 3. Ship to an addressbook address (address chosen from list)

    def reset_shipping_data(self):
        self._flush_namespace('shipping')

    def ship_to_user_address(self, address):
        """
        Set existing shipping address id to session and unset address fields
        from session
        """
        self.reset_shipping_data()
        self._set('shipping', 'user_address_id', address.id)

    def ship_to_new_address(self, address_fields):
        """
        Set new shipping address details to session and unset shipping address
        id
        """
        self._unset('shipping', 'new_address_fields')
        phone_number = address_fields.get('phone_number')
        if phone_number:
            address_fields = address_fields.copy()
            address_fields['phone_number'] = force_text(
                address_fields['phone_number'])
        self._set('shipping', 'new_address_fields', address_fields)

    def new_shipping_address_fields(self):
        """
        Get shipping address fields from session
        """
        return self._get('shipping', 'new_address_fields')

    def shipping_user_address_id(self):
        """
        Get user address id from session
        """
        return self._get('shipping', 'user_address_id')
    user_address_id = shipping_user_address_id

    def is_shipping_address_set(self):
        """
        Test whether a shipping address has been stored in the session.

        This can be from a new address or re-using an existing address.
        """
        new_fields = self.new_shipping_address_fields()
        has_new_address = new_fields is not None
        user_address_id = self.user_address_id()
        has_old_address = user_address_id is not None and user_address_id > 0
        return has_new_address or has_old_address

    # Shipping method
    # ===============

    def use_free_shipping(self):
        """
        Set "free shipping" code to session
        """
        self._set('shipping', 'method_code', '__free__')

    def use_shipping_method(self, code):
        """
        Set shipping method code to session
        """
        self._set('shipping', 'method_code', code)

    def shipping_method_code(self, basket):
        """
        Returns the shipping method code
        """
        return self._get('shipping', 'method_code')

    def shipping_method(self, basket):
        """
        Returns the shipping method model based on the
        data stored in the session.
        """
        warnings.warn((
            "shipping_method is deprecated as the functionality has "
            "been moved to the get_shipping_method from the checkout "
            "session mixin"), DeprecationWarning)
        code = self.shipping_method_code(basket)
        if not code:
            return None
        return Repository().find_by_code(code, basket)

    def is_shipping_method_set(self, basket):
        """
        Test if a valid shipping method is stored in the session
        """
        return self.shipping_method_code(basket) is not None

    # Billing address fields
    # ======================
    #
    # There are 3 common options:
    # 1. Billing address is entered manually through a form
    # 2. Billing address is selected from address book
    # 3. Billing address is the same as the shipping address

    def bill_to_new_address(self, address_fields):
        """
        Store address fields for a billing address.
        """
        self._flush_namespace('billing')
        self._set('billing', 'new_address_fields', address_fields)

    def bill_to_user_address(self, address):
        """
        Set an address from a user's address book as the billing address

        :address: The address object
        """
        self._flush_namespace('billing')
        self._set('billing', 'user_address_id', address.id)

    def bill_to_shipping_address(self):
        """
        Record fact that the billing address is to be the same as
        the shipping address.
        """
        self._flush_namespace('billing')
        self._set('billing', 'billing_address_same_as_shipping', True)

    # Legacy method name
    billing_address_same_as_shipping = bill_to_shipping_address

    def is_billing_address_same_as_shipping(self):
        return self._get('billing', 'billing_address_same_as_shipping', False)

    def billing_user_address_id(self):
        """
        Return the ID of the user address being used for billing
        """
        return self._get('billing', 'user_address_id')

    def new_billing_address_fields(self):
        """
        Return fields for a billing address
        """
        return self._get('billing', 'new_address_fields')

    # Payment methods
    # ===============

    def pay_by(self, method):
        self._set('payment', 'method', method)

    def payment_method(self):
        return self._get('payment', 'method')

    # Submission methods

    def set_order_number(self, order_number):
        self._set('submission', 'order_number', order_number)

    def get_order_number(self):
        return self._get('submission', 'order_number')

    def set_submitted_basket(self, basket):
        self._set('submission', 'basket_id', basket.id)

    def get_submitted_basket_id(self):
        return self._get('submission', 'basket_id')
