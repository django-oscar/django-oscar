# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError

from oscar.apps.catalogue import models
from oscar.apps.catalogue.categories import create_from_breadcrumbs


class TestCategory(TestCase):

    def setUp(self):
        self.products = models.Category.add_root(name="Products")
        self.books = self.products.add_child(name="Books")

    def test_includes_parents_name_in_full_name(self):
        self.assertTrue('Products' in self.books.full_name)

    def test_includes_slug_in_slug(self):
        self.assertTrue(self.products.slug in self.books.slug)

    def test_supports_has_children_method(self):
        """supports has_children method"""
        self.assertTrue(self.products.has_children())

    def test_enforces_slug_uniqueness(self):
        with self.assertRaises(ValidationError):
            self.products.add_child(name="Books")


class TestANonAsciiCategory(TestCase):

    def test_has_a_nonempty_slug(self):
        cat = models.Category.add_root(name=u'διακριτικός')
        self.assertTrue(len(cat.slug) > 0)


class TestMovingACategory(TestCase):

    def setUp(self):
        breadcrumbs = (
            'Books > Fiction > Horror > Teen',
            'Books > Fiction > Horror > Gothic',
            'Books > Fiction > Comedy',
            'Books > Non-fiction > Biography',
            'Books > Non-fiction > Programming',
            'Books > Childrens',
        )
        for trail in breadcrumbs:
            create_from_breadcrumbs(trail)

        horror = models.Category.objects.get(name="Horror")
        programming = models.Category.objects.get(name="Programming")
        horror.move(programming)

        # Reload horror instance to pick up changes
        self.horror = models.Category.objects.get(name="Horror")

    def print_tree(self, tree=None):
        """
        Print out the category tree
        """
        if tree is None:
            tree = models.Category.objects.filter(depth=1)
        for node in tree:
            print node
            self.print_tree(node.get_children())

    def test_updates_instance_name(self):
        self.assertEqual('Books > Non-fiction > Horror',
                         self.horror.full_name)

    def test_updates_subtree_names(self):
        teen = models.Category.objects.get(name="Teen")
        self.assertEqual('Books > Non-fiction > Horror > Teen',
                         teen.full_name)
        gothic = models.Category.objects.get(name="Gothic")
        self.assertEqual('Books > Non-fiction > Horror > Gothic',
                         gothic.full_name)


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
