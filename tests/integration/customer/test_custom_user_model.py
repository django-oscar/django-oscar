from django.test import TestCase
from oscar.core import compat


class TestCustomUserModel(TestCase):

    def test_can_be_created_without_error(self):
        klass = compat.get_user_model()
        try:
            klass.objects.create_user('_', 'a@a.com', 'pa55w0rd')
        except Exception, e:
            self.fail("Unable to create user model: %s" % e)
