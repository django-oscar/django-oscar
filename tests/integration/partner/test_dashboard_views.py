from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from oscar.apps.dashboard.partners import views
from oscar.test.factories import PartnerFactory, PermissionFactory, UserFactory


class TestPartnerUserUnlinkView(TestCase):
    def test_remove_dashboard_permission(self):
        user = UserFactory(is_staff=False)
        permission = PermissionFactory(
            codename="dashboard_access",
            content_type=ContentType.objects.get(app_label="partner", model="partner"),
        )
        user.user_permissions.add(permission)
        partner = PartnerFactory()
        partner.users.add(user)

        view = views.PartnerUserUnlinkView()
        view.unlink_user(user, partner)

        self.assertEqual(partner.users.count(), 0)
        self.assertTrue(Permission.objects.filter(pk=permission.pk).exists())


class TestPartnerUserLinkUnlinkAuthority(TestCase):
    def setUp(self):
        self.partner = PartnerFactory()
        self.other_partner = PartnerFactory()
        self.partner_user = UserFactory(is_staff=False)
        self.partner.users.add(self.partner_user)
        self.target_user = UserFactory(is_staff=False)

    def test_partner_user_cannot_link_user_with_foreign_partner(self):
        view = views.PartnerUserLinkView()
        view.kwargs = {"partner_pk": self.other_partner.pk}
        request = RequestFactory().post("/")
        request.user = self.partner_user

        with self.assertRaises(PermissionDenied):
            view.dispatch(
                request,
                user_pk=self.target_user.pk,
                partner_pk=self.other_partner.pk,
            )

    def test_partner_user_cannot_unlink_user_with_foreign_partner(self):
        self.other_partner.users.add(self.target_user)
        view = views.PartnerUserUnlinkView()
        view.kwargs = {"partner_pk": self.other_partner.pk}
        request = RequestFactory().post("/")
        request.user = self.partner_user

        with self.assertRaises(PermissionDenied):
            view.dispatch(
                request,
                user_pk=self.target_user.pk,
                partner_pk=self.other_partner.pk,
            )
