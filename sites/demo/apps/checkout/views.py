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
        ctx = super(PaymentDetailsView, self).get_context_data(**kwargs)
        if 'bankcard_form' not in kwargs:
            ctx['bankcard_form'] = BankcardForm()
        return ctx

    def handle_payment_details_submission(self, request):
        bankcard_form = BankcardForm(request.POST)
        if bankcard_form.is_valid():
            return self.render_preview(request, bankcard_form=bankcard_form)
        return self.render_payment_details(
            request, bankcard_form=bankcard_form)

    def handle_preview_submission(self, request):
        bankcard_form = BankcardForm(request.POST)
        if not bankcard_form.is_valid():
            # Must be tampering - we don't need to be that friendly with our
            # error message.
            messages.error(request, _("Invalid submission"))
            return http.HttpResponseRedirect(
                reverse('checkout:payment-details'))

        submission = self.build_submission(
            payment_kwargs={'bankcard_form': bankcard_form})
        return self.submit(**submission)

    def handle_payment(self, order_number, total, **kwargs):
        # Make request to DataCash - if there any problems (eg bankcard
        # not valid / request refused by bank) then an exception would be
        # raised and handled by the parent PaymentDetail view)
        facade = Facade()
        bankcard = kwargs['bankcard_form'].bankcard
        datacash_ref = facade.pre_authorise(
            order_number, total.incl_tax, bankcard)

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
