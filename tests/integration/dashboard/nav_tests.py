from django.test import TestCase
from oscar.apps.dashboard.menu import get_nodes
from oscar.core.compat import get_user_model


User = get_user_model()


class TestCategory(TestCase):

    def setUp(self):
        self.staff_user = User.objects.create_user('staff', 'staff@example.com',
                                                   'pw1')
        self.staff_user.is_staff = True
        self.staff_user.save()
        self.non_staff_user = User.objects.create_user('nostaff',
                                                       'nostaff@example.com',
                                                       'pw2')
        self.non_staff_user.save()

    def test_staff_user_has_menu(self):
        menu = get_nodes(self.staff_user)
        self.assertTrue(menu)

    def test_non_staff_user_has_empty_menu(self):
        menu = get_nodes(self.non_staff_user)
        self.assertEqual(menu, [])



