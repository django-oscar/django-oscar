"""
Mobile endpoints that django-oscar-api does not provide, mounted under /api/
before oscarapi.urls (see sandbox/urls.py).
"""

from django.urls import path

from apps.api.views.account import AccountDetail, ChangePassword, PasswordReset
from apps.api.views.cart import (
    CartLineDetail,
    CartLines,
    CartVoucherDetail,
    CartVouchers,
    CartView,
)
from apps.api.views.review import MyReviewList, ProductReviewList
from apps.stripe_checkout.payment_methods import (
    PaymentMethodDetail,
    PaymentMethodList,
    PaymentMethodReturn,
)
from apps.stripe_checkout.views import (
    CheckoutCancel,
    CheckoutReturn,
    CheckoutStatus,
    CheckoutView,
    StripeWebhook,
)

urlpatterns = [
    # before oscarapi's checkout/, which places unpaid orders
    path("checkout/", CheckoutView.as_view(), name="api-checkout"),
    path("checkout/return/", CheckoutReturn.as_view(), name="api-checkout-return"),
    path(
        "checkout/stripe/webhook/",
        StripeWebhook.as_view(),
        name="api-checkout-stripe-webhook",
    ),
    path(
        "checkout/<str:session_id>/",
        CheckoutStatus.as_view(),
        name="api-checkout-status",
    ),
    path(
        "checkout/<str:session_id>/cancel/",
        CheckoutCancel.as_view(),
        name="api-checkout-cancel",
    ),
    path("payment-methods/", PaymentMethodList.as_view(), name="api-payment-methods"),
    path(
        "payment-methods/return/",
        PaymentMethodReturn.as_view(),
        name="api-payment-methods-return",
    ),
    path(
        "payment-methods/<str:payment_method_id>/",
        PaymentMethodDetail.as_view(),
        name="api-payment-method",
    ),
    path("cart/", CartView.as_view(), name="api-cart"),
    path("cart/lines/", CartLines.as_view(), name="api-cart-lines"),
    path("cart/lines/<int:pk>/", CartLineDetail.as_view(), name="api-cart-line"),
    path("cart/vouchers/", CartVouchers.as_view(), name="api-cart-vouchers"),
    path(
        "cart/vouchers/<str:code>/",
        CartVoucherDetail.as_view(),
        name="api-cart-voucher",
    ),
    path(
        "products/<int:pk>/reviews/",
        ProductReviewList.as_view(),
        name="api-product-reviews",
    ),
    path("reviews/mine/", MyReviewList.as_view(), name="api-my-reviews"),
    path("account/", AccountDetail.as_view(), name="api-account"),
    path("account/password/", ChangePassword.as_view(), name="api-account-password"),
    path(
        "account/password-reset/",
        PasswordReset.as_view(),
        name="api-account-password-reset",
    ),
]
