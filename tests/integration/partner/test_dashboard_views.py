from django.contrib.auth.models import Permission
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from oscar.test.factories import PartnerFactory, PermissionFactory, UserFactory
from oscar.apps.dashboard.partners import views


class TestPartnerUserUnlinkView(TestCase):
    def test_remove_dashboard_permission(self):
        user = UserFactory(is_staff=False)
        permission = PermissionFactory(
            codename='dashboard_access',
            content_type=ContentType.objects.get(
                app_label='partner', model='partner'))
        user.user_permissions.add(permission)
        partner = PartnerFactory()
        partner.users.add(user)

        view = views.PartnerUserUnlinkView()
        view.unlink_user(user, partner)

        self.assertEqual(partner.users.count(), 0)
        self.assertTrue(Permission.objects.filter(pk=permission.pk).exists())
