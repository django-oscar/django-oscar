"""
Checkout of the mobile app basket, paid with Stripe Checkout (routed in
apps/api/urls.py, in place of oscarapi's checkout which places unpaid orders):

    GET  checkout/                       totals before paying (delivery included)
    POST checkout/                       {"shipping_address": {...},
                                          "guest_email": "...", "client": "app"|"web"}
                                         -> {"session_id", "url", ...}
    GET  checkout/<session_id>/          payment status, the order once paid
    POST checkout/<session_id>/cancel/   gives the basket back
    GET  checkout/return/                page shown by Stripe after paying (app)
    POST checkout/stripe/webhook/        Stripe events (signed)

The basket is the one of apps/api/views/cart.py (token, or guest session).
"""

import logging

import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from oscarapi.basket import operations
from oscarapi.serializers.checkout import ShippingAddressSerializer
from rest_framework import authentication, permissions, serializers, status, views
from rest_framework.response import Response

from apps.api.views.cart import get_cart
from apps.stripe_checkout import services
from apps.stripe_checkout.models import StripeCheckout

logger = logging.getLogger("apps.stripe_checkout")


class _StartSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    shipping_address = serializers.DictField()
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    client = serializers.ChoiceField(choices=("app", "web"), default="app")


class _CheckoutAPIView(views.APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.AllowAny,)


class CheckoutView(_CheckoutAPIView):
    def get(self, request):
        basket = get_cart(request)
        operations.apply_offers(request, basket)
        return Response(services.summary(basket, request.user, request))

    def post(self, request):
        data = _StartSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        address = ShippingAddressSerializer(
            data=data.validated_data["shipping_address"], context={"request": request}
        )
        if not address.is_valid():
            return Response(
                {"shipping_address": address.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        if request.user.is_authenticated:
            email = request.user.email
        else:
            email = data.validated_data.get("guest_email")
            if not email:
                return Response(
                    {
                        "guest_email": [
                            _("Enter your email address to order as a guest")
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if not services.is_configured():
            return Response(
                {"detail": _("Payment is not available at the moment")},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        basket = get_cart(request)
        operations.apply_offers(request, basket)
        try:
            checkout, url = services.create_checkout(
                request,
                basket,
                email,
                dict(address.validated_data),
                data.validated_data["client"],
            )
        except services.CheckoutError as e:
            return Response(
                {"non_field_errors": [str(e)]}, status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.StripeError:
            logger.exception("Stripe session creation failed")
            return Response(
                {"detail": _("The payment could not be started, please try again")},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        payload = services.status_payload(checkout)
        payload["url"] = url
        return Response(payload, status=status.HTTP_201_CREATED)


class CheckoutStatus(_CheckoutAPIView):
    def get(self, request, session_id):
        checkout = get_object_or_404(StripeCheckout, session_id=session_id)
        try:
            services.sync(checkout)
        except stripe.StripeError:
            # Stripe unreachable: the webhook will update the checkout
            logger.exception("Stripe session %s: status check failed", session_id)
        services.restore_basket(checkout, request)
        return Response(services.status_payload(checkout))


class CheckoutCancel(_CheckoutAPIView):
    def post(self, request, session_id):
        checkout = get_object_or_404(StripeCheckout, session_id=session_id)
        try:
            checkout = services.cancel(checkout)
        except stripe.StripeError:
            logger.exception("Stripe session %s: cancel failed", session_id)
            return Response(
                {"detail": _("The payment could not be canceled, please try again")},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        services.restore_basket(checkout, request)
        return Response(services.status_payload(checkout))


class CheckoutReturn(TemplateView):
    """Shown in the app's in-app browser once Stripe is done"""

    template_name = "stripe_checkout/return.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["canceled"] = "canceled" in self.request.GET
        return ctx


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhook(View):
    EVENTS = (
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
        "checkout.session.expired",
    )

    def post(self, request):
        try:
            event = stripe.Webhook.construct_event(
                request.body,
                request.headers.get("Stripe-Signature", ""),
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.SignatureVerificationError):
            return HttpResponseBadRequest()
        if event["type"] in self.EVENTS:
            session = event["data"]["object"]
            checkout = StripeCheckout.objects.filter(session_id=session["id"]).first()
            if checkout is not None:
                services.apply_session(checkout, session)
        return HttpResponse()
