"""
Cards saved on Stripe for the signed-in user (routed in apps/api/urls.py):

    GET    payment-methods/              the cards, [] before the first one
    POST   payment-methods/              {"client": "app"|"web"}
                                         -> {"session_id", "url"} of a Stripe
                                         page (setup mode) saving a card
    DELETE payment-methods/<pm_id>/      removes a card
    GET    payment-methods/return/       page shown by Stripe afterwards (app)

The cards belong to the user's Stripe Customer (services.customer_id); the
card numbers never reach the shop.
"""

import logging

import stripe
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from rest_framework import authentication, permissions, serializers, status, views
from rest_framework.response import Response

from apps.stripe_checkout import services

logger = logging.getLogger("apps.stripe_checkout")


class _SetupSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    client = serializers.ChoiceField(choices=("app", "web"), default="app")


def card_payload(payment_method):
    card = payment_method["card"]
    return {
        "id": payment_method["id"],
        "brand": card["brand"],
        "last4": card["last4"],
        "exp_month": card["exp_month"],
        "exp_year": card["exp_year"],
        # Stripe objects are not dicts: no .get()
        "name": payment_method["billing_details"]["name"] or "",
    }


def return_urls(request, client):
    """success_url and cancel_url of the setup page, like
    services.return_urls"""
    if client == "web":
        base = request.build_absolute_uri("/app/") + "?payment_method_session="
    else:
        base = (
            request.build_absolute_uri(reverse("api-payment-methods-return"))
            + "?session_id="
        )
    success = base + "{CHECKOUT_SESSION_ID}"
    return success, success + "&canceled=1"


def _unavailable():
    return Response(
        {"detail": _("Payment is not available at the moment")},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _stripe_failed(message):
    return Response({"detail": message}, status=status.HTTP_502_BAD_GATEWAY)


class _PaymentMethodsAPIView(views.APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)


class PaymentMethodList(_PaymentMethodsAPIView):
    def get(self, request):
        customer = (
            services.customer_id(request.user, create=False)
            if services.is_configured()
            else None
        )
        if customer is None:
            return Response([])
        try:
            methods = stripe.Customer.list_payment_methods(
                customer, type="card", limit=100, api_key=settings.STRIPE_SECRET_KEY
            )
        except stripe.StripeError:
            logger.exception("Stripe customer %s: card list failed", customer)
            return _stripe_failed(_("Your cards could not be loaded, please try again"))
        return Response([card_payload(method) for method in methods["data"]])

    def post(self, request):
        data = _SetupSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        if not services.is_configured():
            return _unavailable()
        success_url, cancel_url = return_urls(request, data.validated_data["client"])
        try:
            session = stripe.checkout.Session.create(
                api_key=settings.STRIPE_SECRET_KEY,
                mode="setup",
                customer=services.customer_id(request.user),
                # the payment methods are chosen in the Stripe dashboard
                currency=settings.OSCAR_DEFAULT_CURRENCY.lower(),
                success_url=success_url,
                cancel_url=cancel_url,
                locale="auto",
            )
        except stripe.StripeError:
            logger.exception("Stripe setup session creation failed")
            return _stripe_failed(_("The card could not be added, please try again"))
        return Response(
            {"session_id": session["id"], "url": session["url"]},
            status=status.HTTP_201_CREATED,
        )


class PaymentMethodDetail(_PaymentMethodsAPIView):
    def delete(self, request, payment_method_id):
        customer = (
            services.customer_id(request.user, create=False)
            if services.is_configured()
            else None
        )
        not_found = Response(status=status.HTTP_404_NOT_FOUND)
        if customer is None:
            return not_found
        try:
            method = stripe.PaymentMethod.retrieve(
                payment_method_id, api_key=settings.STRIPE_SECRET_KEY
            )
        except stripe.InvalidRequestError:
            return not_found
        except stripe.StripeError:
            logger.exception(
                "Stripe payment method %s: retrieve failed", payment_method_id
            )
            return _stripe_failed(_("The card could not be removed, please try again"))
        # only the cards of the user's own customer
        if method["customer"] != customer:
            return not_found
        try:
            stripe.PaymentMethod.detach(
                payment_method_id, api_key=settings.STRIPE_SECRET_KEY
            )
        except stripe.StripeError:
            logger.exception(
                "Stripe payment method %s: detach failed", payment_method_id
            )
            return _stripe_failed(_("The card could not be removed, please try again"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentMethodReturn(TemplateView):
    """Shown in the app's in-app browser once the card is saved"""

    template_name = "stripe_checkout/payment_method_return.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["canceled"] = "canceled" in self.request.GET
        return ctx
