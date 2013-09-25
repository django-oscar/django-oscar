from django.core.urlresolvers import reverse
from django_dynamic_fixture import get
from oscar.test.testcases import ClientTestCase

from oscar.apps.dashboard.users.views import IndexView
from oscar.core.compat import get_user_model


User = get_user_model()


class IndexViewTests(ClientTestCase):
    is_staff = True
    active_users_ids = []
    inactive_users_ids = []

    def setUp(self):
        super(IndexViewTests, self).setUp()
        for i in range(1, 25):
            get(User, is_active=True)
        for i in range(1, 25):
            get(User, is_active=False)

        user_queryset = User.objects.all()
        self.active_users_ids = user_queryset.filter(is_active=True).values_list('id', flat=True)
        self.inactive_users_ids = user_queryset.filter(is_active=False).values_list('id', flat=True)

    def test_user_list_view(self):
        response = self.client.get(reverse('dashboard:users-index'))
        self.assertInContext(response, 'user_list')
        self.assertEquals(len(response.context['user_list']), IndexView.paginate_by)

    def test_make_active(self):
        params = {'action': 'make_active',
                  'selected_user': self.inactive_users_ids}
        response = self.client.post(reverse('dashboard:users-index'), params)
        ex_inactive = User.objects.get(id=self.inactive_users_ids[10])
        self.assertIsRedirect(response)
        self.assertTrue(ex_inactive.is_active)

    def test_make_inactive(self):
        params = {'action': 'make_inactive',
                  'selected_user': self.active_users_ids}
        response = self.client.post(reverse('dashboard:users-index'), params)
        ex_active = User.objects.get(id=self.active_users_ids[10])
        self.assertIsRedirect(response)
        self.assertFalse(ex_active.is_active)


class DetailViewTests(ClientTestCase):
    is_staff = True

    def test_user_detail_view(self):
        response = self.client.get(reverse('dashboard:user-detail', kwargs={'pk': 1} ))
        self.assertInContext(response, 'user')
        self.assertIsOk(response)
