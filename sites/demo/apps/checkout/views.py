from django.contrib import messages
from django import http
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from datacash.facade import Facade

from oscar.apps.checkout import views
from oscar.apps.payment.forms import BankcardForm
from oscar.apps.payment.models import SourceType


# Customise the core PaymentDetailsView to integrate Datacash
class PaymentDetailsView(views.PaymentDetailsView):

    def get_context_data(self, **kwargs):
        # Add bankcard form to the template context
        if 'bankcard_form' not in kwargs:
            kwargs['bankcard_form'] = BankcardForm()
        ctx =  super(PaymentDetailsView, self).get_context_data(**kwargs)
        return ctx

    def post(self, request, *args, **kwargs):
        if request.POST.get('action', '') == 'place_order':
            return self.do_place_order(request)

        # Check bankcard form is valid
        bankcard_form = BankcardForm(request.POST)
        if not bankcard_form.is_valid():
            # Bancard form invalid, re-render the payment details template
            self.preview = False
            ctx = self.get_context_data(**kwargs)
            ctx['bankcard_form'] = bankcard_form
            return self.render_to_response(ctx)

        # Render preview page (with completed bankcard form hidden).
        # Note, we don't write the bankcard details to the session or DB
        # as a security precaution.
        return self.render_preview(request, bankcard_form=bankcard_form)

    def do_place_order(self, request):
        # Double-check the bankcard data is still valid
        bankcard_form = BankcardForm(request.POST)
        if not bankcard_form.is_valid():
            # Must be tampering - we don't need to be that friendly with our
            # error message.
            messages.error(request, _("Invalid submission"))
            return http.HttpResponseRedirect(
                reverse('checkout:payment-details'))

        submission = self.build_submission(bankcard_form)
        return self.submit(**submission)

    def build_submission(self, bankcard_form, **kwargs):
        # Modify the default submission dict with the bankcard instance
        submission = super(PaymentDetailsView, self).build_submission()
        if bankcard_form.is_valid():
            submission['payment_kwargs']['bankcard'] = bankcard_form.bankcard
        return submission

    def handle_payment(self, order_number, total, **kwargs):
        # Make request to DataCash - if there any problems (eg bankcard
        # not valid / request refused by bank) then an exception would be
        # raised and handled by the parent PaymentDetail view)
        facade = Facade()
        datacash_ref = facade.pre_authorise(
            order_number, total.incl_tax, kwargs['bankcard'])

        # Request was successful - record the "payment source".  As this
        # request was a 'pre-auth', we set the 'amount_allocated' - if we had
        # performed an 'auth' request, then we would set 'amount_debited'.
        source_type, _ = SourceType.objects.get_or_create(name='Datacash')
        source = source_type.sources.model(
            source_type=source_type,
            currency=total.currency,
            amount_allocated=total.incl_tax,
            reference=datacash_ref)
        self.add_payment_source(source)

        # Also record payment event
        self.add_payment_event(
            'pre-auth', total.incl_tax, reference=datacash_ref)
