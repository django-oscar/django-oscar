from django.core.urlresolvers import reverse
from django.contrib.flatpages.models import FlatPage
from oscar.test.testcases import ClientTestCase


class PageViewTests(ClientTestCase):
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
        self.assertTrue('Password' not in response.content)

    def test_dashboard_page_list(self):
        response = self.client.get(reverse('dashboard:page-list'))
        objects = response.context[-1]['object_list']

        self.assertTrue(self.flatpage_1 in objects)
        self.assertTrue(self.flatpage_2 in objects)

    def test_dashboard_create_page_with_existing_url(self):
        self.assertEquals(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/', data={
                                        'title': 'test',
                                        'url': '/dashboard/pages/',
                                    }, follow=True)

        # Only the two existing flatpages should be saved.
        self.assertEquals(FlatPage.objects.count(), 2)

    def test_dashboard_create_page_with_custom_url(self):
        self.assertEquals(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/create/', data={
            'title': 'Test Page',
            'url': '/test/page/',
            'content': "<h1> Content </h1>"
        }, follow=True)

        self.assertEquals(FlatPage.objects.count(), 3)

        page = FlatPage.objects.get(pk=3)
        self.assertEquals(page.title, 'Test Page')
        self.assertEquals(page.url, '/test/page/')
        self.assertEquals(page.content, "<h1> Content </h1>")
        self.assertEquals(page.sites.count(), 1)

    def test_dashboard_create_page_with_slugified_url(self):
        self.assertEquals(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/create/', data={
                                        'title': 'New Page', 'content': ""
                                    }, follow=True)

        self.assertEquals(FlatPage.objects.count(), 3)

        page = FlatPage.objects.get(pk=3)
        self.assertEquals(page.title, 'New Page')
        self.assertEquals(page.url, '/new-page/')
        self.assertEquals(page.content, "")
        self.assertEquals(page.sites.count(), 1)

    def test_dashboard_create_page_with_exisiting_url_does_not_work(self):
        self.assertEquals(FlatPage.objects.count(), 2)

        self.client.post('/dashboard/pages/create/', data={
                                        'title': 'New Page', 'content': ""
                                    }, follow=True)

        self.client.post('/dashboard/pages/create/', data={
                                        'title': 'New Page', 'content': ""
                                    }, follow=True)

        self.assertEquals(FlatPage.objects.count(), 3)

    def test_dashboard_update_page_valid_url(self):
        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/test/page/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEquals(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEquals(page.title, 'Test Page')
        self.assertEquals(page.url, '/test/page/')
        self.assertEquals(page.content, "<h1> Content </h1>")
        self.assertEquals(page.sites.count(), 1)

    def test_dashboard_update_page_invalid_url(self):
        self.assertEquals(self.flatpage_1.title, 'title1')

        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/url2/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEquals(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEquals(page.title, 'title1')
        self.assertEquals(page.url, '/url1/')
        self.assertEquals(page.content, "some content")

    def test_dashboard_update_page_valid_url_unchanged(self):
        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/url1/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEquals(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEquals(page.title, 'Test Page')
        self.assertEquals(page.url, '/url1/')
        self.assertEquals(page.content, "<h1> Content </h1>")

        # now only update the URL
        self.client.post('/dashboard/pages/update/1/', data={
                                        'title': 'Test Page',
                                        'url': '/new/url/',
                                        'content': "<h1> Content </h1>"
                                    }, follow=True)

        self.assertEquals(FlatPage.objects.count(), 2)

        page = FlatPage.objects.get(pk=1)
        self.assertEquals(page.title, 'Test Page')
        self.assertEquals(page.url, '/new/url/')
        self.assertEquals(page.content, "<h1> Content </h1>")

    def test_dashboard_delete_pages(self):
        self.client.post('/dashboard/pages/delete/1/', follow=True)

        self.assertEquals(FlatPage.objects.count(), 1)

        page = FlatPage.objects.get(pk=2)
        self.assertEquals(page.title, 'title2')
        self.assertEquals(page.url, '/url2/')
        self.assertEquals(page.content, "other content")
