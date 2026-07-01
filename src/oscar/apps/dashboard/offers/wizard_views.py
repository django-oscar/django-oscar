import json

from django.contrib import messages
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from oscar.core.loading import get_model

ConditionalOffer = get_model("offer", "ConditionalOffer")


class OfferWizardStepView(FormView):
    wizard_name = "offer_wizard"
    form_class = None
    step_name = None
    update = False
    url_name = None
    success_url_name = "dashboard:offer-list"

    # Keep a reference to previous view class to allow checks to be made on
    # whether prior steps have been completed
    previous_view = None

    # pylint: disable=attribute-defined-outside-init
    def dispatch(self, request, *args, **kwargs):
        if self.update:
            self.offer = get_object_or_404(ConditionalOffer, id=kwargs["pk"])
        if not self.is_previous_step_complete(request):
            messages.warning(
                request,
                _("%s step not complete") % (self.previous_view.step_name.title(),),
            )
            return HttpResponseRedirect(reverse(self.previous_view.url_name))
        return super().dispatch(request, *args, **kwargs)

    def is_previous_step_complete(self, request):
        if not self.previous_view:
            return True
        return self.previous_view.is_valid(self, request)

    def _key(self, step_name=None, is_object=False):
        key = step_name if step_name else self.step_name
        if self.update:
            key += str(self.offer.id)
        if is_object:
            key += "_obj"
        return key

    def _store_form_kwargs(self, form):
        session_data = self.request.session.setdefault(self.wizard_name, {})

        # Adjust kwargs to avoid trying to save the range instance
        form_data = form.cleaned_data.copy()
        product_range = form_data.get("range")
        if product_range is not None:
            form_data["range"] = product_range.id

        form_kwargs = {"data": form_data}
        json_data = json.dumps(form_kwargs, cls=DjangoJSONEncoder)

        session_data[self._key()] = json_data
        self.request.session.save()

    def _fetch_form_kwargs(self):
        session_data = self.request.session.setdefault(self.wizard_name, {})
        json_data = session_data.get(self._key(self.step_name), None)
        if json_data:
            return json.loads(json_data)

        return {}

    def _store_object(self, form):
        session_data = self.request.session.setdefault(self.wizard_name, {})

        # We don't store the object instance as that is not JSON serialisable.
        # Instead, we save an alternative form
        instance = form.save(commit=False)
        # remove fields that do not exist (yet) on the uncommitted instance, i.e. m2m fields
        cleanfields = [field.name for field in instance._meta.local_fields]

        json_qs = serializers.serialize("json", [instance], fields=tuple(cleanfields))

        session_data[self._key(is_object=True)] = json_qs
        self.request.session.save()

    def _fetch_object(self, step_name, request=None):
        if request is None:
            request = self.request
        session_data = request.session.setdefault(self.wizard_name, {})
        json_qs = session_data.get(self._key(step_name, is_object=True), None)
        if json_qs:
            # Recreate model instance from passed data
            deserialised_obj = list(serializers.deserialize("json", json_qs))
            return deserialised_obj[0].object

    def _fetch_session_offer(self):
        """Return the offer instance loaded with the data stored in the session.

        When updating an offer, the updated fields are used with the existing
        offer data.
        """
        offer = self._fetch_object("metadata")
        if offer is None and self.update:
            offer = self.offer
        return offer

    def _flush_session(self):
        self.request.session[self.wizard_name] = {}
        self.request.session.save()

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = {}
        if self.update:
            form_kwargs["instance"] = self.get_instance()
        session_kwargs = self._fetch_form_kwargs()
        form_kwargs.update(session_kwargs)
        parent_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs.update(parent_kwargs)
        return form_kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.update:
            ctx["offer"] = self.offer
        ctx["session_offer"] = self._fetch_session_offer()
        ctx["title"] = self.get_title()
        return ctx

    def get_title(self):
        return self.step_name.title()

    def form_valid(self, form):
        self._store_form_kwargs(form)
        self._store_object(form)

        if self.update and "save" in form.data:
            # Save changes to this offer when updating and pressed save button
            return self.save_offer(self.offer)
        else:
            # Proceed to next page
            return super().form_valid(form)

    def save_offer(self, offer):
        # We update the offer with the name/description/offer_type from step 1
        session_offer = self._fetch_session_offer()
        offer.name = session_offer.name
        offer.description = session_offer.description
        offer.offer_type = session_offer.offer_type

        # Save the related models, then save the offer.
        # Note than you can save already on the first page of the wizard,
        # so le'ts check if the benefit and condition exist
        benefit = self._fetch_object("benefit")
        if benefit:
            benefit.save()
            offer.benefit = benefit

        condition = self._fetch_object("condition")
        if condition:
            condition.save()
            offer.condition = condition

        offer.save()

        self._flush_session()

        if self.update:
            msg = _("Offer '%s' updated") % offer.name
        else:
            msg = _("Offer '%s' created!") % offer.name
        messages.success(self.request, msg)

        return HttpResponseRedirect(
            reverse("dashboard:offer-detail", kwargs={"pk": offer.pk})
        )

    def get_success_url(self):
        if self.update:
            return reverse(self.success_url_name, kwargs={"pk": self.kwargs["pk"]})
        return reverse(self.success_url_name)

    @classmethod
    def is_valid(cls, current_view, request):
        if current_view.update:
            return True
        return current_view._fetch_object(cls.step_name, request) is not None
