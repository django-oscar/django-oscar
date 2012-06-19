from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings

from oscar.apps.catalogue.models import Product, ProductClass, Category, \
        ProductAttribute
from oscar.apps.catalogue.categories import create_from_breadcrumbs


class CategoryTests(TestCase):

    def setUp(self):
        Category.objects.all().delete()
    
    def test_creating_category_root(self):
        trail = 'Books'
        category = create_from_breadcrumbs(trail)
        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Books')
        self.assertEquals(category.slug, 'books')      
    
    def test_creating_parent_and_child_categories(self):
        trail = 'Books > Science-Fiction'
        category = create_from_breadcrumbs(trail)
        
        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Science-Fiction')
        self.assertEquals(category.get_depth(), 2)
        self.assertEquals(category.get_parent().name, 'Books')
        self.assertEquals(2, Category.objects.count())
        self.assertEquals(category.slug, 'books/science-fiction')
        
    def test_creating_multiple_categories(self):
        trail = 'Books > Science-Fiction > Star Trek'
        create_from_breadcrumbs(trail)
        trail = 'Books > Factual > Popular Science'
        category = create_from_breadcrumbs(trail)        
        
        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Popular Science')
        self.assertEquals(category.get_depth(), 3)
        self.assertEquals(category.get_parent().name, 'Factual')        
        self.assertEquals(5, Category.objects.count())
        self.assertEquals(category.slug, 'books/factual/popular-science', )        

    def test_alternative_separator_can_be_used(self):
        trail = 'Food|Cheese|Blue'
        create_from_breadcrumbs(trail, separator='|')
        self.assertEquals(3, len(Category.objects.all()))

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
        category = Category.objects.get(name='A')

        category.move(target, pos='first-child')

        c1 = Category.objects.get(name='A')
        self.assertEqual(c1.slug, 't/a')
        self.assertEqual(c1.full_name, 'T > A')

        child = Category.objects.get(name='F')
        self.assertEqual(child.slug, 't/a/e/f')
        self.assertEqual(child.full_name, 'T > A > E > F')

        child = Category.objects.get(name='D')
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

        category = Category.objects.get(name='E')
        target = Category.objects.get(name='A')

        category.move(target, pos='right')

        child = Category.objects.get(name='E')
        self.assertEqual(child.slug, 'e')
        self.assertEqual(child.full_name, 'E')

        child = Category.objects.get(name='F')
        self.assertEqual(child.slug, 'e/f')
        self.assertEqual(child.full_name, 'E > F')


class ProductTests(TestCase):

    def setUp(self):
        self.product_class,_ = ProductClass.objects.get_or_create(name='Clothing')


class ProductCreationTests(ProductTests):

    def setUp(self):
        super(ProductCreationTests, self).setUp()
        ProductAttribute.objects.create(product_class=self.product_class,
                                        name='Number of pages',
                                        code='num_pages',
                                        type='integer')
        Product.ENABLE_ATTRIBUTE_BINDING = True

    def tearDown(self):
        Product.ENABLE_ATTRIBUTE_BINDING = False

    def test_create_products_with_attributes(self):
        product = Product(upc='1234',
                          product_class=self.product_class,
                          title='testing')
        product.attr.num_pages = 100
        product.save()
   

class TopLevelProductTests(ProductTests):
    
    def test_top_level_products_must_have_titles(self):
        self.assertRaises(ValidationError, Product.objects.create, product_class=self.product_class)
        
        
class VariantProductTests(ProductTests):
    
    def setUp(self):
        super(VariantProductTests, self).setUp()
        self.parent = Product.objects.create(title="Parent product", product_class=self.product_class)
    
    def test_variant_products_dont_need_titles(self):
        p = Product.objects.create(parent=self.parent, product_class=self.product_class)
        
    def test_variant_products_dont_need_a_product_class(self):
        p = Product.objects.create(parent=self.parent)
        
    def test_variant_products_inherit_parent_titles(self):
        p = Product.objects.create(parent=self.parent, product_class=self.product_class)
        self.assertEquals("Parent product", p.get_title())
        
    def test_variant_products_inherit_product_class(self):
        p = Product.objects.create(parent=self.parent)
        self.assertEquals("Clothing", p.get_product_class().name)


class SingleProductViewTest(TestCase):
    fixtures = ['sample-products']
    
    def setUp(self):
        self.client = Client()
        
    def test_canonical_urls_are_enforced(self):
        p = Product.objects.get(id=1)
        args = {'product_slug': 'wrong-slug',
                'pk': p.id}
        wrong_url = reverse('catalogue:detail', kwargs=args)
        response = self.client.get(wrong_url)
        self.assertEquals(301, response.status_code)
