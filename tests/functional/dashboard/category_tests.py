from django.core.urlresolvers import reverse
from django.test import TestCase
from django_dynamic_fixture import G

from oscar.test.testcases import WebTestCase
from oscar.core.compat import get_user_model
from oscar.apps.catalogue.models import Category
from oscar.apps.dashboard.catalogue.forms import CategoryForm
from oscar.apps.catalogue.categories import create_from_breadcrumbs


User = get_user_model()

def create_test_category_tree():
    trail = 'A > B > C'
    create_from_breadcrumbs(trail)
    trail = 'A > B > D'
    create_from_breadcrumbs(trail)
    trail = 'A > E > F'
    create_from_breadcrumbs(trail)
    trail = 'A > E > G'
    create_from_breadcrumbs(trail)


class TestCategoryForm(TestCase):

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


class TestCategoryDashboard(WebTestCase):

    def setUp(self):
        self.staff = G(User, is_staff=True)
        create_from_breadcrumbs('A > B > C')

    def test_redirects_to_main_dashboard_after_creating_top_level_category(self):
        a = Category.objects.get(name='A')
        category_add = self.app.get(reverse('dashboard:catalogue-category-create'),
                                    user=self.staff)
        form = category_add.form
        form['name'] = 'Top-level category'
        form['_position'] = 'right'
        form['_ref_node_id'] = a.id
        response = form.submit()
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-category-list'))

    def test_redirects_to_parent_list_after_creating_child_category(self):
        b = Category.objects.get(name='B')
        c = Category.objects.get(name='C')
        category_add = self.app.get(reverse('dashboard:catalogue-category-create'),
                                    user=self.staff)
        form = category_add.form
        form['name'] = 'Child category'
        form['_position'] = 'left'
        form['_ref_node_id'] = c.id
        response = form.submit()
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-category-detail-list',
                                    args=(b.pk,)))

    def test_handles_invalid_form_gracefully(self):
        dashboard_index = self.app.get(reverse('dashboard:index'),
                                       user=self.staff)
        category_index = dashboard_index.click("Categories")
        category_add = category_index.click("Create new category")
        response = category_add.form.submit()
        self.assertEqual(200, response.status_code)
