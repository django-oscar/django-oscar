from django.core.urlresolvers import reverse
from django.contrib.flatpages.models import FlatPage
from oscar.test.testcases import WebTestCase


class TestPageDashboard(WebTestCase):
    is_anonymous = False
    is_staff = True

    def setUp(self):
        self.flatpage_1 = FlatPage.objects.create(
            title='title1', url='/url1/',
            content='some content')
        self.flatpage_2 = FlatPage.objects.create(
            title='title2', url='/url2/',
            content='other content')

        super(TestPageDashboard, self).setUp()

    def test_dashboard_index_is_for_staff_only(self):
        response = self.get(reverse('dashboard:page-list'))
        self.assertTrue('Password' not in response.content.decode('utf8'))

    def test_dashboard_page_list(self):
        response = self.get(reverse('dashboard:page-list'))
        objects = response.context[-1]['object_list']

        self.assertTrue(self.flatpage_1 in objects)
        self.assertTrue(self.flatpage_2 in objects)

    def test_doesnt_allow_existing_pages_to_be_clobbered(self):
        self.assertEqual(FlatPage.objects.count(), 2)

        page = self.get(reverse('dashboard:page-create'))
        form = page.form
        form['title'] = 'test'
        form['url'] = '/dashboard/pages/'
        response = form.submit()
        self.assertEqual(200, response.status_code)
        self.assertEqual("Specified page already exists!",
                         response.context['form'].errors['url'][0])
        self.assertEqual(FlatPage.objects.count(), 2)

    def test_allows_page_to_be_created(self):
        page = self.get(reverse('dashboard:page-create'))
        form = page.form
        form['title'] = 'test'
        form['url'] = '/my-new-url/'
        form['content'] = 'my content here'
        response = form.submit()

        self.assertIsRedirect(response)
        self.assertEqual(FlatPage.objects.count(), 3)

    def test_dashboard_create_page_with_slugified_url(self):
        page = self.get(reverse('dashboard:page-create'))
        form = page.form
        form['title'] = 'test'
        form['content'] = 'my content here'
        response = form.submit()

        self.assertIsRedirect(response)
        self.assertEqual(FlatPage.objects.count(), 3)

    def test_dashboard_create_page_with_exisiting_url_does_not_work(self):
        page = self.get(reverse('dashboard:page-create'))
        form = page.form
        form['title'] = 'test'
        form['url'] = '/url1/'  # already exists
        form['content'] = 'my content here'
        response = form.submit()

        self.assertEqual(200, response.status_code)
        self.assertEqual("Specified page already exists!",
                         response.context['form'].errors['url'][0])
        self.assertEqual(FlatPage.objects.count(), 2)

    def test_dashboard_update_page_valid_url(self):
        page = self.get(reverse('dashboard:page-update',
                                kwargs={'pk': self.flatpage_1.pk}))
        form = page.form
        form['title'] = 'test'
        form['url'] = '/new/url/'  # already exists
        form['content'] = 'my content here'
        response = form.submit()

        self.assertIsRedirect(response)

        page = FlatPage.objects.get(pk=self.flatpage_1.pk)
        self.assertEqual(page.title, 'test')
        self.assertEqual(page.url, '/new/url/')
        self.assertEqual(page.content, "my content here")
        self.assertEqual(page.sites.count(), 1)

    def test_dashboard_update_page_invalid_url(self):
        page = self.get(reverse('dashboard:page-update',
                                kwargs={'pk': self.flatpage_1.pk}))
        form = page.form
        form['url'] = '/url2/'  # already exists
        response = form.submit()

        self.assertEqual(200, response.status_code)
        self.assertEqual("Specified page already exists!",
                         response.context['form'].errors['url'][0])

    def test_dashboard_delete_pages(self):
        page = self.get(reverse('dashboard:page-list'))
        delete_page = page.click(linkid="delete_page_%s" % self.flatpage_1.id)
        response = delete_page.form.submit()

        self.assertIsRedirect(response)
        self.assertEqual(FlatPage.objects.count(), 1)
