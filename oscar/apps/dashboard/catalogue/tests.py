from django.core.urlresolvers import reverse
from django.test import TestCase

from oscar.test import ClientTestCase
from oscar.apps.catalogue.models import Category
from oscar.apps.dashboard.catalogue.forms import CategoryForm
from oscar.apps.catalogue.categories import create_from_breadcrumbs


class ViewTests(ClientTestCase):
    is_staff = True

    def test_pages_exist(self):
        urls = [reverse('dashboard:catalogue-product-list'),
                reverse('dashboard:catalogue-category-list'),
                reverse('dashboard:stock-alert-list'),
               ]
        for url in urls:
            self.assertIsOk(self.client.get(url))


def create_test_category_tree():
    trail = 'A > B > C'
    create_from_breadcrumbs(trail)
    trail = 'A > B > D'
    create_from_breadcrumbs(trail)
    trail = 'A > E > F'
    create_from_breadcrumbs(trail)
    trail = 'A > E > G'
    create_from_breadcrumbs(trail)


class CategoryFormTests(TestCase):

    def setUp(self):
        Category.objects.all().delete()

    def test_conflicting_slugs_recognized(self):
        create_test_category_tree()

        f = CategoryForm()

        #root categories
        ref_node_pk = Category.objects.get(name='A').pk
        conflicting = f.is_slug_conflicting('A', ref_node_pk, 'right')
        self.assertEqual(conflicting, True)

        conflicting = f.is_slug_conflicting('A', None, 'left')
        self.assertEqual(conflicting, True)

        conflicting = f.is_slug_conflicting('A', None, 'first-child')
        self.assertEqual(conflicting, True)

        conflicting = f.is_slug_conflicting('B', None, 'left')
        self.assertEqual(conflicting, False)

        #subcategories
        ref_node_pk = Category.objects.get(name='C').pk
        conflicting = f.is_slug_conflicting('D', ref_node_pk, 'left')
        self.assertEqual(conflicting, True)

        ref_node_pk = Category.objects.get(name='B').pk
        conflicting = f.is_slug_conflicting('D', ref_node_pk, 'first-child')
        self.assertEqual(conflicting, True)

        ref_node_pk = Category.objects.get(name='F').pk
        conflicting = f.is_slug_conflicting('D', ref_node_pk, 'left')
        self.assertEqual(conflicting, False)

        ref_node_pk = Category.objects.get(name='E').pk
        conflicting = f.is_slug_conflicting('D', ref_node_pk, 'first-child')
        self.assertEqual(conflicting, False)

        #updating
        f.instance = Category.objects.get(name='E')
        ref_node_pk = Category.objects.get(name='A').pk
        conflicting = f.is_slug_conflicting('E', ref_node_pk, 'first-child')
        self.assertEqual(conflicting, False)


class CategoryTests(ClientTestCase):
    is_staff = True

    def setUp(self):
        super(CategoryTests, self).setUp()
        create_test_category_tree()

    def test_category_create(self):
        a = Category.objects.get(name='A')
        b = Category.objects.get(name='B')
        c = Category.objects.get(name='C')

        #Redirect to subcategory list view
        response = self.client.post(reverse('dashboard:catalogue-category-create'),
                                            {'name': 'Testee',
                                             '_position': 'left',
                                             '_ref_node_id': c.id,})

        self.assertIsRedirect(response, reverse('dashboard:catalogue-category-detail-list', 
                                                args=(b.pk,)))

        #Redirect to main category list view
        response = self.client.post(reverse('dashboard:catalogue-category-create'),
                                            {'name': 'Testee',
                                             '_position': 'right',
                                             '_ref_node_id': a.id,})

        self.assertIsRedirect(response, reverse('dashboard:catalogue-category-list'))

        self.assertEqual(Category.objects.all().count(), 9)
