from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue import models
from oscar.apps.catalogue.categories import create_from_breadcrumbs


class TestCategory(TestCase):

    def test_supports_has_children_method(self):
        """Supports has_children method"""
        root = models.Category.add_root(name="Products")
        self.assertFalse(root.has_children())
        root.add_child(name="Books")
        self.assertTrue(root.has_children())

    def test_enforces_slug_uniqueness(self):
        root = models.Category.add_root(name="Products")
        root.add_child(name="Books")
        with self.assertRaises(ValidationError):
            root.add_child(name="Books")


class TestCategoryFactory(TestCase):

    def setUp(self):
        models.Category.objects.all().delete()

    def test_can_create_single_level_category(self):
        trail = 'Books'
        category = create_from_breadcrumbs(trail)
        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Books')
        self.assertEquals(category.slug, 'books')

    def test_can_create_parent_and_child_categories(self):
        trail = 'Books > Science-Fiction'
        category = create_from_breadcrumbs(trail)

        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Science-Fiction')
        self.assertEquals(category.get_depth(), 2)
        self.assertEquals(category.get_parent().name, 'Books')
        self.assertEquals(2, models.Category.objects.count())
        self.assertEquals(category.slug, 'books/science-fiction')

    def test_can_create_multiple_categories(self):
        trail = 'Books > Science-Fiction > Star Trek'
        create_from_breadcrumbs(trail)
        trail = 'Books > Factual > Popular Science'
        category = create_from_breadcrumbs(trail)

        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Popular Science')
        self.assertEquals(category.get_depth(), 3)
        self.assertEquals(category.get_parent().name, 'Factual')
        self.assertEquals(5, models.Category.objects.count())
        self.assertEquals(category.slug, 'books/factual/popular-science', )

    def test_can_use_alternative_separator(self):
        trail = 'Food|Cheese|Blue'
        create_from_breadcrumbs(trail, separator='|')
        self.assertEquals(3, len(models.Category.objects.all()))

    def test_updating_subtree_slugs_when_moving_category_to_new_parent(self):
        trail = 'A > B > C'
        create_from_breadcrumbs(trail)
        trail = 'A > B > D'
        create_from_breadcrumbs(trail)
        trail = 'A > E > F'
        create_from_breadcrumbs(trail)
        trail = 'A > E > G'
        create_from_breadcrumbs(trail)

        trail = 'T'
        target = create_from_breadcrumbs(trail)
        category = models.Category.objects.get(name='A')

        category.move(target, pos='first-child')

        c1 = models.Category.objects.get(name='A')
        self.assertEqual(c1.slug, 't/a')
        self.assertEqual(c1.full_name, 'T > A')

        child = models.Category.objects.get(name='F')
        self.assertEqual(child.slug, 't/a/e/f')
        self.assertEqual(child.full_name, 'T > A > E > F')

        child = models.Category.objects.get(name='D')
        self.assertEqual(child.slug, 't/a/b/d')
        self.assertEqual(child.full_name, 'T > A > B > D')

    def test_updating_subtree_when_moving_category_to_new_sibling(self):
        trail = 'A > B > C'
        create_from_breadcrumbs(trail)
        trail = 'A > B > D'
        create_from_breadcrumbs(trail)
        trail = 'A > E > F'
        create_from_breadcrumbs(trail)
        trail = 'A > E > G'
        create_from_breadcrumbs(trail)

        category = models.Category.objects.get(name='E')
        target = models.Category.objects.get(name='A')

        category.move(target, pos='right')

        child = models.Category.objects.get(name='E')
        self.assertEqual(child.slug, 'e')
        self.assertEqual(child.full_name, 'E')

        child = models.Category.objects.get(name='F')
        self.assertEqual(child.slug, 'e/f')
        self.assertEqual(child.full_name, 'E > F')
