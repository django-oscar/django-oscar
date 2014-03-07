from django.core.urlresolvers import reverse
from django.contrib.flatpages.models import FlatPage
from oscar.test.testcases import WebTestCase


class PageViewTests(WebTestCase):
    is_anonymous = False
    is_staff = True

    def setUp(self):
        self.flatpage_1 = FlatPage.objects.create(title='title1', url='/url1/',
                                      content='some content')
        self.flatpage_2 = FlatPage.objects.create(title='title2', url='/url2/',
                                      content='other content')

        super(PageViewTests, self).setUp()

    def test_dashboard_index_is_for_staff_only(self):
        response = self.client.get(reverse('dashboard:page-list'))
        self.assertTrue('Password' not in response.content.decode('utf8'))

    def test_dashboard_page_list(self):
        response = self.client.get(reverse('dashboard:page-list'))
        objects = response.context[-1]['object_list']

        self.assertTrue(self.flatpage_1 in objects)
        self.assertTrue(self.flatpage_2 in objects)

    def test_dashboard_create_page_with_existing_url(self):
        self.assertEqual(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/', data={
                                        'title': 'test',
                                        'url': '/dashboard/pages/',
                                    }, follow=True)

        # Only the two existing flatpages should be saved.
        self.assertEqual(FlatPage.objects.count(), 2)

    def test_dashboard_create_page_with_custom_url(self):
        self.assertEqual(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/create/', data={
            'title': 'Test Page',
            'url': '/test/page/',
            'content': "<h1> Content </h1>"
        }, follow=True)

        self.assertEqual(FlatPage.objects.count(), 3)

        page = FlatPage.objects.get(pk=3)
        self.assertEqual(page.title, 'Test Page')
        self.assertEqual(page.url, '/test/page/')
        self.assertEqual(page.content, "<h1> Content </h1>")
        self.assertEqual(page.sites.count(), 1)

    def test_dashboard_create_page_with_slugified_url(self):
        self.assertEqual(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/create/', data={
                                        'title': 'New Page', 'content': ""
                                    }, follow=True)

        self.assertEqual(FlatPage.objects.count(), 3)

        page = FlatPage.objects.get(pk=3)
        self.assertEqual(page.title, 'New Page')
        self.assertEqual(page.url, '/new-page/')
        self.assertEqual(page.content, "")
        self.assertEqual(page.sites.count(), 1)

    def test_dashboard_create_page_with_exisiting_url_does_not_work(self):
        self.assertEqual(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/create/', data={
                                        'title': 'New Page', 'content': ""
                                    }, follow=True)

        self.client.post('/dashboard/pages/create/', data={
                                        'title': 'New Page', 'content': ""
                                    }, follow=True)

        self.assertEqual(FlatPage.objects.count(), 3)

    def test_dashboard_update_page_valid_url(self):
        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/test/page/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEqual(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEqual(page.title, 'Test Page')
        self.assertEqual(page.url, '/test/page/')
        self.assertEqual(page.content, "<h1> Content </h1>")
        self.assertEqual(page.sites.count(), 1)

    def test_dashboard_update_page_invalid_url(self):
        self.assertEqual(self.flatpage_1.title, 'title1')

        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/url2/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEqual(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEqual(page.title, 'title1')
        self.assertEqual(page.url, '/url1/')
        self.assertEqual(page.content, "some content")

    def test_dashboard_update_page_valid_url_unchanged(self):
        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/url1/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEqual(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEqual(page.title, 'Test Page')
        self.assertEqual(page.url, '/url1/')
        self.assertEqual(page.content, "<h1> Content </h1>")

        # now only update the URL
        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/new/url/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEqual(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEqual(page.title, 'Test Page')
        self.assertEqual(page.url, '/new/url/')
        self.assertEqual(page.content, "<h1> Content </h1>")

    def test_dashboard_delete_pages(self):
        self.client.post('/dashboard/pages/delete/1/', follow=True)

        self.assertEqual(FlatPage.objects.count(), 1)

        page = FlatPage.objects.get(pk=2)
        self.assertEqual(page.title, 'title2')
        self.assertEqual(page.url, '/url2/')
        self.assertEqual(page.content, "other content")
