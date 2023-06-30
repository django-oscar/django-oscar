from django.contrib.flatpages.models import FlatPage
from django.test import TestCase
from django.urls import reverse

from oscar.apps.dashboard.pages.forms import PageUpdateForm
from oscar.test.testcases import WebTestCase


class TestPageDashboard(WebTestCase):
    is_anonymous = False
    is_staff = True

    def setUp(self):
        self.flatpage_1 = FlatPage.objects.create(
            title="title1", url="/url1/", content="some content"
        )
        self.flatpage_2 = FlatPage.objects.create(
            title="title2", url="/url2/", content="other content"
        )

        super().setUp()

    def test_dashboard_index_is_for_staff_only(self):
        response = self.get(reverse("dashboard:page-list"))
        self.assertTrue("Password" not in response.content.decode("utf8"))

    def test_dashboard_page_list(self):
        response = self.get(reverse("dashboard:page-list"))
        objects = response.context[-1]["object_list"]

        self.assertTrue(self.flatpage_1 in objects)
        self.assertTrue(self.flatpage_2 in objects)

    def test_dashboard_delete_pages(self):
        page = self.get(reverse("dashboard:page-list"))
        delete_page = page.click(linkid="delete_page_%s" % self.flatpage_1.id)
        response = delete_page.form.submit()

        self.assertIsRedirect(response)
        self.assertEqual(FlatPage.objects.count(), 1)

    def test_dashboard_create_page_with_slugified_url(self):
        page = self.get(reverse("dashboard:page-create"))
        form = page.form
        form["title"] = "test"
        form["content"] = "my content here"
        response = form.submit()

        self.assertIsRedirect(response)

    def test_dashboard_create_page_with_duplicate_slugified_url_fails(self):
        page = self.get(reverse("dashboard:page-create"))
        form = page.form
        form["title"] = "url1"  # This will slugify to url1
        form["content"] = "my content here"
        response = form.submit()

        self.assertEqual(200, response.status_code)

    def test_default_site_added_for_new_pages(self):
        page = self.get(reverse("dashboard:page-create"))
        form = page.form
        form["title"] = "test"
        form["url"] = "/hello-world/"
        form.submit()

        p = FlatPage.objects.get(url="/hello-world/")
        self.assertEqual(p.sites.count(), 1)


class DashboardPageUpdateFormTestCase(TestCase):
    def setUp(self):
        self.flatpage_1 = FlatPage.objects.create(
            title="title1", url="/url1/", content="some content"
        )
        self.flatpage_2 = FlatPage.objects.create(
            title="title2", url="/url2/", content="other content"
        )

    def test_doesnt_allow_existing_pages_to_be_clobbered(self):
        form = PageUpdateForm(
            data={
                "title": "test",
                "url": "/dashboard/pages/",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["url"], ["Specified page already exists!"])

    def test_allows_page_to_be_created(self):
        form = PageUpdateForm(
            data={"title": "test", "url": "/my-new-url/", "content": "my content here"}
        )

        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(FlatPage.objects.count(), 3)

    def test_create_page_with_slugified_url(self):
        form = PageUpdateForm(data={"title": "test", "content": "my content here"})

        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(FlatPage.objects.count(), 3)

    def test_create_page_with_existing_url_does_not_work(self):
        form = PageUpdateForm(
            data={
                "title": "test",
                "url": "/url1/",  # already exists
                "content": "my content here",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["url"], ["Specified page already exists!"])

    def test_update_page_valid_url(self):
        form = PageUpdateForm(
            instance=self.flatpage_1,
            data={"title": "test", "url": "/new/url/", "content": "my content here"},
        )

        form.save()

        self.flatpage_1.refresh_from_db()
        page = self.flatpage_1
        self.assertEqual(page.title, "test")
        self.assertEqual(page.url, "/new/url/")
        self.assertEqual(page.content, "my content here")

    def test_invalid_chars_in_url(self):
        form = PageUpdateForm(
            data={
                "url": "/%* /",
                "title": "Title",
                "content": "Content",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["url"],
            [
                "This value must contain only letters, numbers, dots, underscores, dashes, slashes or tildes."
            ],
        )

    def test_invalid_url_length(self):
        form = PageUpdateForm(
            data={
                "url": "/this_url_is_more_than_100_characters_long_which_is_invalid"
                "_because_the_model_field_has_a_max_length_of_100",
                "title": "Title",
                "content": "Content",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["url"],
            ["Ensure this value has at most 100 characters (it has 107)."],
        )
