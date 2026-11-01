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

urlpatterns = [
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
    path(
        "account/password/", ChangePassword.as_view(), name="api-account-password"
    ),
    path(
        "account/password-reset/",
        PasswordReset.as_view(),
        name="api-account-password-reset",
    ),
]
