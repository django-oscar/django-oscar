"""
Account settings for the mobile app (not provided by django-oscar-api).
Routed in apps/api/urls.py.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from oscar.core.loading import get_class
from rest_framework import generics, permissions, serializers, status, views
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

PasswordResetForm = get_class("customer.forms", "PasswordResetForm")


class AccountSerializer(serializers.ModelSerializer):
    """Same fields as GET /api/login/ (OSCARAPI_USER_FIELDS); only the name
    can be changed, the email identifies the account"""

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "date_joined")
        read_only_fields = ("id", "email", "date_joined")


class AccountDetail(generics.RetrieveUpdateAPIView):
    """GET / PATCH the signed-in user's name"""

    serializer_class = AccountSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "patch", "options")

    def get_object(self):
        return self.request.user


class ChangePassword(views.APIView):
    """
    POST ``old_password``, ``new_password1``, ``new_password2``: Django's
    password change form, so AUTH_PASSWORD_VALIDATORS apply. Answers 204, or
    400 with the form errors. The DRF token stays valid.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        form = PasswordChangeForm(request.user, request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        form.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordReset(views.APIView):
    """
    POST ``email``: sends Oscar's password reset email, whose link opens the
    website page where the new password is chosen. Answers 204 whether or
    not an account uses this email, so accounts cannot be discovered; 400
    for an invalid email. Throttled (``password_reset`` rate).
    """

    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "password_reset"

    def post(self, request):
        form = PasswordResetForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        form.save(request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)
