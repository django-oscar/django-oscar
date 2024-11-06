from django.contrib.auth import get_user_model
from django.urls import reverse

from oscar.core.loading import get_class
from oscar.test.testcases import WebTestCase, add_permissions
from oscar.test.factories import ProductFactory

User = get_user_model()
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class CatalogueDashboardPermissionTests(WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()
        self.product = ProductFactory()
        self.client.force_login(self.user)

    def test_product_createupdate_view_access(self):
        url = reverse("dashboard:catalogue-product", kwargs={"pk": self.product.id})

        # Staff user without permissions should get 403 Forbidden
        self.assertNoAccess(self.client.get(url))

        # Assign permission to a staff
        add_permissions(self.user, DashboardPermission.product)

        # Staff user with permission should get 200 OK
        self.assertIsOk(self.client.get(url))
