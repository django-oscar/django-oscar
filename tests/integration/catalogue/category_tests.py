# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from django import template

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
        self.assertEqual(category.name, 'Books')
        self.assertEqual(category.slug, 'books')

    def test_can_create_parent_and_child_categories(self):
        trail = 'Books > Science-Fiction'
        category = create_from_breadcrumbs(trail)

        self.assertIsNotNone(category)
        self.assertEqual(category.name, 'Science-Fiction')
        self.assertEqual(category.get_depth(), 2)
        self.assertEqual(category.get_parent().name, 'Books')
        self.assertEqual(2, models.Category.objects.count())
        self.assertEqual(category.slug, 'books/science-fiction')

    def test_can_create_multiple_categories(self):
        trail = 'Books > Science-Fiction > Star Trek'
        create_from_breadcrumbs(trail)
        trail = 'Books > Factual > Popular Science'
        category = create_from_breadcrumbs(trail)

        self.assertIsNotNone(category)
        self.assertEqual(category.name, 'Popular Science')
        self.assertEqual(category.get_depth(), 3)
        self.assertEqual(category.get_parent().name, 'Factual')
        self.assertEqual(5, models.Category.objects.count())
        self.assertEqual(category.slug, 'books/factual/popular-science', )

    def test_can_use_alternative_separator(self):
        trail = 'Food|Cheese|Blue'
        create_from_breadcrumbs(trail, separator='|')
        self.assertEqual(3, len(models.Category.objects.all()))

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


class TestCategoryTemplateTags(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCategoryTemplateTags, self).__init__(*args, **kwargs)
        self.template = """
          {% if tree_categories %}
              <ul>
              {% for tree_category, info in tree_categories %}
                  <li>
                  {% if tree_category.pk == category.pk %}
                      <strong>{{ tree_category.name }}</strong>
                  {% else %}
                      <a href="{{ tree_category.get_absolute_url }}">
                          {{ tree_category.name }}</a>
                  {% endif %}
                  {% if info.has_children %}<ul>{% else %}</li>{% endif %}
                  {% for n in info.num_to_close %}
                      </ul></li>
                  {% endfor %}
              {% endfor %}
              </ul>
          {% endif %}
        """

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

    def render_template(self, template_string, context={}):
        """
        Return the rendered string or raise an exception.
        """
        tpl = template.Template(template_string)
        ctxt = template.Context(context)
        return tpl.render(ctxt)

    def test_all_categories(self):
        template = """
        {% load category_tags %}
        {% category_tree as tree_categories %}
        """ + self.template
        rendered = self.render_template(template)
        categories_exists = set(('Books', 'Fiction', 'Horror', 'Teen',
            'Gothic', 'Comedy', 'Non-fiction', 'Biography', 'Programming',
            'Childrens'))
        for c in categories_exists:
            self.assertTrue(c in rendered)

    def test_categories_depth(self):
        template = """
        {% load category_tags %}
        {% category_tree depth=1 as tree_categories %}
        """ + self.template
        rendered = self.render_template(template)
        categories_exists = set(('Books', ))
        for c in categories_exists:
            self.assertTrue(c in rendered)
        categories_missed = set(('Fiction', 'Horror', 'Teen', 'Gothic',
            'Comedy', 'Non-fiction', 'Biography', 'Programming', 'Childrens'))
        for c in categories_missed:
            self.assertFalse(c in rendered)

    def test_categories_parent(self):
        template = """
        {% load category_tags %}
        {% category_tree parent=category as tree_categories %}
        """ + self.template
        rendered = self.render_template(template,
            context={'category': models.Category.objects.get(name="Fiction")})
        categories_exists = set(('Horror', 'Teen', 'Gothic', 'Comedy'))
        for c in categories_exists:
            self.assertTrue(c in rendered)
        categories_missed = set(('Books', 'Fiction', 'Non-fiction',
            'Biography', 'Programming', 'Childrens'))
        for c in categories_missed:
            self.assertFalse(c in rendered)

    def test_categories_depth_parent(self):
        template = """
        {% load category_tags %}
        {% category_tree depth=1 parent=category as tree_categories %}
        """ + self.template
        rendered = self.render_template(template,
            context={'category': models.Category.objects.get(name="Fiction")})
        categories_exists = set(('Horror', 'Comedy'))
        for c in categories_exists:
            self.assertTrue(c in rendered)
        categories_missed = set(('Books', 'Fiction', 'Teen', 'Gothic',
            'Non-fiction', 'Biography', 'Programming', 'Childrens'))
        for c in categories_missed:
            self.assertFalse(c in rendered)
