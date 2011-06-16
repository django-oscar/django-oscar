
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from oscar.apps.product.models import Item, ItemClass, Category
from oscar.apps.product.utils import breadcrumbs_to_category


class CategoryTests(TestCase):
    
    def test_create_category_root(self):
        trail = 'Books'
        category = breadcrumbs_to_category(trail)
        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Books')
        self.assertEquals(category.slug, 'books')      
    
    def test_subcategory(self):
        trail = 'Books > Science-Fiction'
        category = breadcrumbs_to_category(trail)
        
        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Science-Fiction')
        self.assertEquals(category.get_depth(), 2)
        self.assertEquals(category.get_parent().name, 'Books')
        self.assertEquals(2, Category.objects.count())
        self.assertEquals(category.slug, 'books/science-fiction')
        
    def test_subsubcategory(self):
        trail = 'Books > Science-Fiction > Star Trek'
        breadcrumbs_to_category(trail)
        trail = 'Books > Factual > Popular Science'
        category = breadcrumbs_to_category(trail)        
        
        self.assertIsNotNone(category)
        self.assertEquals(category.name, 'Popular Science')
        self.assertEquals(category.get_depth(), 3)
        self.assertEquals(category.get_parent().name, 'Factual')        
        self.assertEquals(5, Category.objects.count())
        self.assertEquals(category.slug, 'books/factual/popular-science', )        


class ItemTests(TestCase):

    def setUp(self):
        self.item_class,_ = ItemClass.objects.get_or_create(name='Clothing')
   

class TopLevelItemTests(ItemTests):
    
    def test_top_level_products_must_have_titles(self):
        self.assertRaises(ValidationError, Item.objects.create, item_class=self.item_class)
        
        
class VariantItemTests(ItemTests):
    
    def setUp(self):
        super(VariantItemTests, self).setUp()
        self.parent = Item.objects.create(title="Parent product", item_class=self.item_class)
    
    def test_variant_products_dont_need_titles(self):
        p = Item.objects.create(parent=self.parent, item_class=self.item_class)
        
    def test_variant_products_dont_need_a_product_class(self):
        p = Item.objects.create(parent=self.parent)
        
    def test_variant_products_inherit_parent_titles(self):
        p = Item.objects.create(parent=self.parent, item_class=self.item_class)
        self.assertEquals("Parent product", p.get_title())
        
    def test_variant_products_inherit_product_class(self):
        p = Item.objects.create(parent=self.parent)
        self.assertEquals("Clothing", p.get_item_class().name)


class SingleProductViewTest(TestCase):
    fixtures = ['sample-products']
    
    def setUp(self):
        self.client = Client()
        
    def test_canonical_urls_are_enforced(self):
        p = Item.objects.get(id=1)
        args = {'item_slug': 'wrong-slug',
                'pk': p.id}
        wrong_url = reverse('products:detail', kwargs=args)
        response = self.client.get(wrong_url)
        self.assertEquals(301, response.status_code)