from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import new, get, F

from oscar.test import ClientTestCase

from oscar.apps.dashboard.users.views import IndexView


class IndexViewTests(ClientTestCase):
    is_staff = True

    def setUp(self):
        super(IndexViewTests, self).setUp()
        for i in range(1, 50):
            get(User)

    def test_user_list_view(self):
        response = self.client.get(reverse('dashboard:users-index'))
        self.assertInContext(response, 'user_list')
        self.assertEquals(len(response.context['user_list']), IndexView.paginate_by)

