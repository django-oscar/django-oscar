import datetime
import os
import posixpath
import shutil

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from six import BytesIO
from webtest import Upload

from oscar.apps.catalogue.models import Product, ProductAttribute
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model
from oscar.test import factories
from oscar.test.factories import (
    CategoryFactory, ProductAttributeFactory, ProductClassFactory,
    ProductFactory)
from oscar.test.testcases import WebTestCase

User = get_user_model()
ProductImage = get_model('catalogue', 'ProductImage')


class ProductWebTest(WebTestCase):
    is_staff = True

    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             email='test@email.com',
                                             password='somefancypassword')
        self.user.is_staff = self.is_staff
        self.user.save()

    def get(self, url, **kwargs):
        kwargs['user'] = self.user
        return self.app.get(url, **kwargs)


class TestGatewayPage(ProductWebTest):
    is_staff = True

    def test_redirects_to_list_page_when_no_query_param(self):
        url = reverse('dashboard:catalogue-product-create')
        response = self.get(url)
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-product-list'))

    def test_redirects_to_list_page_when_invalid_query_param(self):
        url = reverse('dashboard:catalogue-product-create')
        response = self.get(url + '?product_class=bad')
        self.assertRedirects(response,
                             reverse('dashboard:catalogue-product-list'))

    def test_redirects_to_form_page_when_valid_query_param(self):
        pclass = ProductClassFactory(name='Books', slug='books')
        url = reverse('dashboard:catalogue-product-create')
        response = self.get(url + '?product_class=%s' % pclass.pk)
        expected_url = reverse('dashboard:catalogue-product-create',
                               kwargs={'product_class_slug': pclass.slug})
        self.assertRedirects(response, expected_url)


class TestCreateParentProduct(ProductWebTest):
    is_staff = True

    def setUp(self):
        self.pclass = ProductClassFactory(name='Books', slug='books')
        super().setUp()

    def submit(self, title=None, category=None, upc=None):
        url = reverse('dashboard:catalogue-product-create',
                      kwargs={'product_class_slug': self.pclass.slug})

        product_form = self.get(url).form

        product_form['title'] = title
        product_form['upc'] = upc
        product_form['structure'] = 'parent'

        if category:
            product_form['productcategory_set-0-category'] = category.id

        return product_form.submit()

    def test_title_is_required(self):
        response = self.submit(title='')

        self.assertContains(response, "must have a title")
        self.assertEqual(Product.objects.count(), 0)

    def test_requires_a_category(self):
        response = self.submit(title="Nice T-Shirt")
        self.assertContains(response, "must have at least one category")
        self.assertEqual(Product.objects.count(), 0)

    def test_for_smoke(self):
        category = CategoryFactory()
        response = self.submit(title='testing', category=category)
        self.assertIsRedirect(response)
        self.assertEqual(Product.objects.count(), 1)

    def test_doesnt_allow_duplicate_upc(self):
        ProductFactory(parent=None, upc="12345")
        category = CategoryFactory()
        self.assertTrue(Product.objects.get(upc="12345"))

        response = self.submit(title="Nice T-Shirt", category=category,
                               upc="12345")

        self.assertEqual(Product.objects.count(), 1)
        self.assertNotEqual(Product.objects.get(upc='12345').title,
                            'Nice T-Shirt')
        self.assertContains(response,
                            "Product with this UPC already exists.")


class TestCreateChildProduct(ProductWebTest):
    is_staff = True

    def setUp(self):
        self.pclass = ProductClassFactory(name='Books', slug='books')
        self.parent = ProductFactory(structure='parent', stockrecords=[])
        super().setUp()

    def test_categories_are_not_required(self):
        url = reverse('dashboard:catalogue-product-create-child',
                      kwargs={'parent_pk': self.parent.pk})
        page = self.get(url)

        product_form = page.form
        product_form['title'] = expected_title = 'Nice T-Shirt'
        product_form.submit()

        try:
            product = Product.objects.get(title=expected_title)
        except Product.DoesNotExist:
            self.fail('creating a child product did not work')

        self.assertEqual(product.parent, self.parent)


class TestProductUpdate(ProductWebTest):

    def test_product_update_form(self):
        self.product = factories.ProductFactory()
        url = reverse('dashboard:catalogue-product',
                      kwargs={'pk': self.product.id})

        page = self.get(url)
        product_form = page.form
        product_form['title'] = expected_title = 'Nice T-Shirt'
        page = product_form.submit()

        product = Product.objects.get(id=self.product.id)

        self.assertEqual(page.context['product'], self.product)
        self.assertEqual(product.title, expected_title)


class TestProductClass(ProductWebTest):
    def setUp(self):
        super().setUp()
        self.pclass = ProductClassFactory(name='T-Shirts', slug='tshirts')

        for attribute_type, __ in ProductAttribute.TYPE_CHOICES:
            values = {
                'type': attribute_type, 'code': attribute_type,
                'product_class': self.pclass, 'name': attribute_type,
            }
            if attribute_type == ProductAttribute.OPTION:
                option_group = factories.AttributeOptionGroupFactory()
                self.option = factories.AttributeOptionFactory(group=option_group)
                values['option_group'] = option_group
            elif attribute_type == ProductAttribute.MULTI_OPTION:
                option_group = factories.AttributeOptionGroupFactory()
                self.multi_option = factories.AttributeOptionFactory(group=option_group)
                values['option_group'] = option_group
            ProductAttributeFactory(**values)
        self.product = factories.ProductFactory(product_class=self.pclass)
        self.url = reverse('dashboard:catalogue-product',
                           kwargs={'pk': self.product.id})
        self.image_folder = datetime.datetime.now().strftime(settings.OSCAR_IMAGE_FOLDER)

    def tearDown(self):
        root_image_folder = self.image_folder.split(os.sep)[0]
        shutil.rmtree(posixpath.join(settings.MEDIA_ROOT, root_image_folder), ignore_errors=True)

    def generate_test_image(self, name):
        tempfile = BytesIO()
        image = Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
        image.save(tempfile, "PNG")
        tempfile.seek(0)
        return tempfile.read()

    def test_product_update_attribute_values(self):
        page = self.get(self.url)
        product_form = page.form
        # Send string field values due to an error
        # in the Webtest during multipart form encode.
        product_form['attr_text'] = 'test1'
        product_form['attr_integer'] = '1'
        product_form['attr_float'] = '1.2'
        product_form['attr_boolean'] = 'yes'
        product_form['attr_richtext'] = 'longread'
        product_form['attr_date'] = '2016-10-12'
        product_form['attr_file'] = Upload('file1.txt', b"test", 'text/plain')
        product_form['attr_image'] = Upload('image1.png', self.generate_test_image('image1.png'), 'image/png')
        product_form.submit()

        # Reloading model instance to re-initiate ProductAttributeContainer
        # with new attributes.
        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.attr.text, 'test1')
        self.assertEqual(self.product.attr.integer, 1)
        self.assertEqual(self.product.attr.float, 1.2)
        self.assertTrue(self.product.attr.boolean)
        self.assertEqual(self.product.attr.richtext, 'longread')
        self.assertEqual(self.product.attr.date, datetime.date(2016, 10, 12))
        self.assertEqual(self.product.attr.file.name, posixpath.join(self.image_folder, 'file1.txt'))
        self.assertEqual(self.product.attr.image.name, posixpath.join(self.image_folder, 'image1.png'))

        page = self.get(self.url)
        product_form = page.form
        product_form['attr_text'] = 'test2'
        product_form['attr_integer'] = '2'
        product_form['attr_float'] = '5.2'
        product_form['attr_boolean'] = ''
        product_form['attr_richtext'] = 'article'
        product_form['attr_date'] = '2016-10-10'
        product_form['attr_file'] = Upload('file2.txt', b"test", 'text/plain')
        product_form['attr_image'] = Upload('image2.png', self.generate_test_image('image2.png'), 'image/png')
        product_form.submit()

        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.attr.text, 'test2')
        self.assertEqual(self.product.attr.integer, 2)
        self.assertEqual(self.product.attr.float, 5.2)
        self.assertFalse(self.product.attr.boolean)
        self.assertEqual(self.product.attr.richtext, 'article')
        self.assertEqual(self.product.attr.date, datetime.date(2016, 10, 10))
        self.assertEqual(self.product.attr.file.name, posixpath.join(self.image_folder, 'file2.txt'))
        self.assertEqual(self.product.attr.image.name, posixpath.join(self.image_folder, 'image2.png'))


class TestProductImages(ProductWebTest):

    def setUp(self):
        super().setUp()
        self.product = factories.ProductFactory()
        self.url = reverse('dashboard:catalogue-product',
                           kwargs={'pk': self.product.id})
        self.image_folder = timezone.now().strftime(settings.OSCAR_IMAGE_FOLDER)

    def tearDown(self):
        root_image_folder = self.image_folder.split(os.sep)[0]
        shutil.rmtree(root_image_folder, ignore_errors=True)

    def generate_test_image(self, name):
        tempfile = BytesIO()
        image = Image.new("RGBA", size=(50, 50), color=(256, 0, 0))
        image.save(tempfile, "PNG")
        tempfile.seek(0)
        return tempfile.read()

    def test_product_images_upload(self):
        page = self.get(self.url)
        product_form = page.form
        product_form['images-0-original'] = Upload('image1.png', self.generate_test_image('image1.png'), 'image/png')
        product_form['images-1-original'] = Upload('image2.png', self.generate_test_image('image2.png'), 'image/png')
        product_form.submit(name='action', value='continue').follow()
        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.images.count(), 2)
        page = self.get(self.url)
        product_form = page.form
        product_form['images-2-original'] = Upload('image3.png', self.generate_test_image('image3.png'), 'image/png')
        product_form.submit()
        self.product = Product.objects.get(pk=self.product.id)
        self.assertEqual(self.product.images.count(), 3)
        images = self.product.images.all()
        self.assertEqual(images[0].original.name, os.path.join(self.image_folder, 'image1.png'))
        self.assertEqual(images[0].display_order, 0)
        self.assertEqual(images[1].original.name, os.path.join(self.image_folder, 'image2.png'))
        self.assertEqual(images[1].display_order, 1)
        self.assertEqual(images[2].original.name, os.path.join(self.image_folder, 'image3.png'))
        self.assertEqual(images[2].display_order, 2)

    def test_product_images_reordering(self):
        im1 = factories.ProductImageFactory(product=self.product, display_order=1)
        im2 = factories.ProductImageFactory(product=self.product, display_order=2)
        im3 = factories.ProductImageFactory(product=self.product, display_order=3)

        self.assertEqual(
            list(ProductImage.objects.all().order_by("display_order")),
            [im1, im2, im3]
        )

        page = self.get(self.url)
        product_form = page.form
        product_form['images-1-display_order'] = '3'  # 1 is im2
        product_form['images-2-display_order'] = '4'  # 2 is im3
        product_form['images-0-display_order'] = '5'  # 0 is im1
        product_form.submit()

        self.assertEqual(
            list(ProductImage.objects.all().order_by("display_order")),
            [im2, im3, im1]
        )
