from django.test import RequestFactory, TestCase

from oscar.templatetags.sorting_tags import anchor


class SortingTagsTestCase(TestCase):
    def test_anchor_tag_output(self):
        ctx = {"request": RequestFactory().get("/")}
        # No title supplied
        self.assertEqual(anchor(ctx, "foo"), '<a href="/?sort=foo">Foo</a>')
        # Title supplied
        self.assertEqual(anchor(ctx, "foo", "Title"), '<a href="/?sort=foo">Title</a>')
        # Title supplied with unsafe chars
        self.assertEqual(
            anchor(ctx, "foo", "Ti&tle"), '<a href="/?sort=foo">Ti&amp;tle</a>'
        )
        # Reverse sort order
        ctx = {"request": RequestFactory().get("/?sort=foo&dir=asc")}
        self.assertEqual(
            anchor(ctx, "foo"),
            '<a href="/?sort=foo&dir=desc">Foo <i class="fas fa-chevron-up"></i></a>',
        )
