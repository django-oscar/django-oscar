from django.test import TestCase
from django.contrib.auth import get_user_model

from oscar.core.loading import get_class
from oscar.test.factories import UserFactory, create_order

User = get_user_model()
UserTable = get_class("dashboard.users.tables", "UserTable")


class UserTableTestCase(TestCase):
    def test_num_orders_sort(self):
        user1 = UserFactory()
        user2 = UserFactory()
        create_order(user=user2)
        table = UserTable(data=User.objects.all())
        table.order_by = "num_orders"
        self.assertEqual(table.data[0].id, user1.id)
        table.order_by = "-num_orders"
        # User2 has with num_orders value of 1
        self.assertEqual(table.data[0].id, user2.id)
