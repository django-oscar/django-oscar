import json

from django.conf import settings
from django.contrib.messages import ERROR, INFO
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.six.moves import http_client
from django.utils.translation import ugettext

from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    AttributeOptionFactory, AttributeOptionGroupFactory, CategoryFactory,
    PartnerFactory, ProductAttributeFactory, ProductFactory, create_product)
from oscar.test.testcases import WebTestCase, add_permissions

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
ProductCategory = get_model('catalogue', 'ProductCategory')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'stockrecord')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeOption = get_model('catalogue', 'AttributeOption')

AttributeOptionGroupForm = get_class('dashboard.catalogue.forms',
                                     'AttributeOptionGroupForm')
AttributeOptionFormSet = get_class('dashboard.catalogue.formsets',
                                   'AttributeOptionFormSet')
RelatedFieldWidgetWrapper = get_class('dashboard.widgets',
                                      'RelatedFieldWidgetWrapper')


class TestCatalogueViews(WebTestCase):
    is_staff = True

    def test_exist(self):
        urls = [reverse('dashboard:catalogue-product-list'),
                reverse('dashboard:catalogue-category-list'),
                reverse('dashboard:stock-alert-list')]
        for url in urls:
            self.assertIsOk(self.get(url))

    def test_upc_filter(self):
        product1 = create_product(upc='123')
        product2 = create_product(upc='12')
        product3 = create_product(upc='1')

        # no value for upc, all results
        page = self.get("%s?upc=" %
                        reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertIn(product3, products_on_page)

        # filter by upc, one result
        page = self.get("%s?upc=123" %
                        reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # exact match, one result, no multiple
        page = self.get("%s?upc=12" %
                        reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertNotIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # part of the upc, one result
        page = self.get("%s?upc=3" %
                        reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)

        # part of the upc, two results
        page = self.get("%s?upc=2" %
                        reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)
        self.assertNotIn(product3, products_on_page)


class TestAStaffUser(WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestAStaffUser, self).setUp()
        self.partner = PartnerFactory()

    def test_can_create_a_product_without_stockrecord(self):
        category = CategoryFactory()
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['productcategory_set-0-category'] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_create_and_continue_editing_a_product(self):
        category = CategoryFactory()
        product_class = ProductClass.objects.create(name="Book")
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['productcategory_set-0-category'] = category.id
        form['stockrecords-0-partner'] = self.partner.id
        form['stockrecords-0-partner_sku'] = '14'
        form['stockrecords-0-num_in_stock'] = '555'
        form['stockrecords-0-price_excl_tax'] = '13.99'
        page = form.submit(name='action', value='continue')

        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.all()[0]
        self.assertEqual(product.stockrecords.all()[0].partner, self.partner)
        self.assertRedirects(page, reverse('dashboard:catalogue-product',
                                           kwargs={'pk': product.id}))

    def test_can_update_a_product_without_stockrecord(self):
        new_title = u'foobar'
        category = CategoryFactory()
        product = ProductFactory(stockrecords=[])

        page = self.get(
            reverse('dashboard:catalogue-product',
                    kwargs={'pk': product.id})
        )
        form = page.forms[0]
        form['productcategory_set-0-category'] = category.id
        self.assertNotEqual(form['title'].value, new_title)
        form['title'] = new_title
        form.submit()

        try:
            product = Product.objects.get(pk=product.pk)
        except Product.DoesNotExist:
            pass
        else:
            self.assertTrue(product.title == new_title)
            if product.has_stockrecords:
                self.fail('Product has stock records but should not')

    def test_can_create_product_with_required_attributes(self):
        category = CategoryFactory()
        attribute = ProductAttributeFactory(required=True)
        product_class = attribute.product_class
        page = self.get(reverse('dashboard:catalogue-product-create',
                                args=(product_class.slug,)))
        form = page.form
        form['upc'] = '123456'
        form['title'] = 'new product'
        form['attr_weight'] = '5'
        form['productcategory_set-0-category'] = category.id
        form.submit()

        self.assertEqual(Product.objects.count(), 1)

    def test_can_delete_a_standalone_product(self):
        product = create_product(partner_users=[self.user])
        category = Category.add_root(name='Test Category')
        ProductCategory.objects.create(category=category, product=product)

        page = self.get(reverse('dashboard:catalogue-product-delete',
                                args=(product.id,))).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(StockRecord.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(ProductCategory.objects.count(), 0)

    def test_can_delete_a_parent_product(self):
        parent_product = create_product(structure='parent')
        create_product(parent=parent_product)

        url = reverse(
            'dashboard:catalogue-product-delete',
            args=(parent_product.id,))
        page = self.get(url).form.submit()

        self.assertRedirects(page, reverse('dashboard:catalogue-product-list'))
        self.assertEqual(Product.objects.count(), 0)

    def test_can_delete_a_child_product(self):
        parent_product = create_product(structure='parent')
        child_product = create_product(parent=parent_product)

        url = reverse(
            'dashboard:catalogue-product-delete',
            args=(child_product.id,))
        page = self.get(url).form.submit()

        expected_url = reverse(
            'dashboard:catalogue-product', kwargs={'pk': parent_product.pk})
        self.assertRedirects(page, expected_url)
        self.assertEqual(Product.objects.count(), 1)

    def test_can_list_her_products(self):
        product1 = create_product(partner_users=[self.user, ])
        product2 = create_product(partner_name="sneaky", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertIn(product2, products_on_page)

    def test_can_create_a_child_product(self):
        parent_product = create_product(structure='parent')
        url = reverse(
            'dashboard:catalogue-product-create-child',
            kwargs={'parent_pk': parent_product.pk})
        form = self.get(url).form
        form.submit()

        self.assertEqual(Product.objects.count(), 2)

    def test_cant_create_child_product_for_invalid_parents(self):
        # Creates a product with stockrecords.
        invalid_parent = create_product(partner_users=[self.user])
        self.assertFalse(invalid_parent.can_be_parent())
        url = reverse(
            'dashboard:catalogue-product-create-child',
            kwargs={'parent_pk': invalid_parent.pk})
        self.assertRedirects(
            self.get(url), reverse('dashboard:catalogue-product-list'))


class TestANonStaffUser(TestAStaffUser):
    is_staff = False
    is_anonymous = False
    permissions = ['partner.dashboard_access', ]

    def setUp(self):
        super(TestANonStaffUser, self).setUp()
        add_permissions(self.user, self.permissions)
        self.partner.users.add(self.user)

    def test_can_list_her_products(self):
        product1 = create_product(partner_name="A", partner_users=[self.user])
        product2 = create_product(partner_name="B", partner_users=[])
        page = self.get(reverse('dashboard:catalogue-product-list'))
        products_on_page = [row.record for row
                            in page.context['products'].page.object_list]
        self.assertIn(product1, products_on_page)
        self.assertNotIn(product2, products_on_page)

    def test_cant_create_a_child_product(self):
        parent_product = create_product(structure='parent')
        url = reverse(
            'dashboard:catalogue-product-create-child',
            kwargs={'parent_pk': parent_product.pk})
        response = self.get(url, status='*')
        self.assertEqual(http_client.FORBIDDEN, response.status_code)

    # Tests below can't work because they don't create a stockrecord

    def test_can_create_a_product_without_stockrecord(self):
        pass

    def test_can_update_a_product_without_stockrecord(self):
        pass

    def test_can_create_product_with_required_attributes(self):
        pass

    # Tests below can't work because child products aren't supported with the
    # permission-based dashboard

    def test_can_delete_a_child_product(self):
        pass

    def test_can_delete_a_parent_product(self):
        pass

    def test_can_create_a_child_product(self):
        pass

    def test_cant_create_child_product_for_invalid_parents(self):
        pass


class AttributeOptionGroupCreateMixin(object):

    def _set_up_display_create_form_vars(self):
        self.url_name = 'dashboard:catalogue-attribute-option-group-create'
        self.title = ugettext("Add a new Attribute Option Group")

    def _test_display_create_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, 'dashboard/catalogue/attribute_option_group_form.html')
        self.assertInContext(response, 'form')
        self.assertIsInstance(response.context['form'], AttributeOptionGroupForm)
        self.assertTrue(response.context['form'].instance._state.adding)
        self.assertInContext(response, 'attribute_option_formset')
        self.assertIsInstance(response.context['attribute_option_formset'], AttributeOptionFormSet)
        self.assertTrue(response.context['attribute_option_formset'].instance._state.adding)
        self.assertInContext(response, 'title')
        self.assertEqual(response.context['title'], self.title)

    def _set_up_create_vars(self):
        self.url_name = 'dashboard:catalogue-attribute-option-group-create'
        self.attribute_option_group_name = 'Test Attribute Option Group'
        self.attribute_option_option = 'Test Attribute Option'

    def _set_up_create_success_vars(self):
        self.success_url_name = 'dashboard:catalogue-attribute-option-group-list'
        self.success_message = ugettext("Attribute Option Group created successfully")

    def _test_creation_of_objects(self):
        # Test the creation of the attribute option group
        self.assertEqual(1, AttributeOptionGroup.objects.all().count())
        attribute_option_group = AttributeOptionGroup.objects.first()
        self.assertEqual(attribute_option_group.name, self.attribute_option_group_name)

        # Test the creation of the attribute option
        self.assertEqual(1, AttributeOption.objects.all().count())
        attribute_option = AttributeOption.objects.first()
        self.assertEqual(attribute_option.group, attribute_option_group)
        self.assertEqual(attribute_option.option, self.attribute_option_option)


class AttributeOptionGroupUpdateMixin(object):

    def _set_up_display_update_form_vars(self):
        url_name = 'dashboard:catalogue-attribute-option-group-update'
        self.url = reverse(url_name, kwargs={'pk': self.attribute_option_group.pk})
        self.title = ugettext("Update Attribute Option Group '%s'") % self.attribute_option_group.name

    def _test_display_update_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, 'dashboard/catalogue/attribute_option_group_form.html')
        self.assertInContext(response, 'form')
        self.assertIsInstance(response.context['form'], AttributeOptionGroupForm)
        self.assertEqual(response.context['form'].instance, self.attribute_option_group)
        self.assertInContext(response, 'attribute_option_formset')
        self.assertIsInstance(response.context['attribute_option_formset'], AttributeOptionFormSet)
        self.assertEqual(response.context['attribute_option_formset'].initial_forms[0].instance, self.attribute_option_group.options.first())
        self.assertInContext(response, 'title')
        self.assertEqual(response.context['title'], self.title)

    def _set_up_update_vars(self):
        url_name = 'dashboard:catalogue-attribute-option-group-update'
        self.url = reverse(url_name, kwargs={'pk': self.attribute_option_group.pk})
        self.attribute_option_group_name = 'Test Attribute Option Group'
        self.attribute_option_option = 'Test Attribute Option'

    def _set_up_update_success_vars(self):
        self.success_url_name = 'dashboard:catalogue-attribute-option-group-list'
        self.success_message = ugettext("Attribute Option Group updated successfully")

    def _test_update_of_objects(self):
        # Test the update of the attribute option group
        attribute_option_group = AttributeOptionGroup.objects.first()
        self.assertEqual(attribute_option_group.name, self.attribute_option_group_name)

        # Test the update of the attribute option
        self.assertEqual(attribute_option_group.options.first().option, self.attribute_option_option)


class AttributeOptionGroupDeleteMixin(object):

    def _set_up_display_delete_form_vars(self):
        url_name = 'dashboard:catalogue-attribute-option-group-delete'
        self.url = reverse(url_name, kwargs={'pk': self.attribute_option_group.pk})

    def _set_up_display_delete_form_allowed_vars(self):
        self.title = ugettext("Delete Attribute Option Group '%s'") % self.attribute_option_group.name

    def _set_up_display_delete_form_disallowed_vars(self):
        self.title = ugettext("Unable to delete '%s'") % self.attribute_option_group.name
        self.error_message = ugettext("1 product attributes are still assigned to this attribute option group")

    def _test_display_delete_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, 'dashboard/catalogue/attribute_option_group_delete.html')
        self.assertInContext(response, 'title')
        self.assertEqual(response.context['title'], self.title)

    def _test_display_delete_disallowed_response(self):
        response = self.response

        self.assertInContext(response, 'disallow')
        self.assertTrue(response.context['disallow'])
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(messages[0].message, self.error_message)

    def _set_up_delete_vars(self):
        url_name = 'dashboard:catalogue-attribute-option-group-delete'
        self.url = reverse(url_name, kwargs={'pk': self.attribute_option_group.pk})

    def _set_up_delete_success_vars(self):
        self.success_url_name = 'dashboard:catalogue-attribute-option-group-list'
        self.success_message = ugettext("Attribute Option Group deleted successfully")

    def _test_deletion_of_objects(self):
        # Test the deletion of the attribute option group
        attribute_option_group_exists = AttributeOptionGroup.objects.exists()
        self.assertFalse(attribute_option_group_exists)

        # Test the deletion of the attribute option
        attribute_option_exists = AttributeOption.objects.exists()
        self.assertFalse(attribute_option_exists)


class AttributeOptionGroupPopUpWindowMixin(object):

    def _set_up_pop_up_window_vars(self):
        self.to_field = AttributeOptionGroup._meta.pk.name
        self.is_popup = RelatedFieldWidgetWrapper.IS_POPUP_VALUE
        self.to_field_var = RelatedFieldWidgetWrapper.TO_FIELD_VAR
        self.is_popup_var = RelatedFieldWidgetWrapper.IS_POPUP_VAR

    def _test_display_pop_up_window_response(self):
        response = self.response

        self.assertInContext(response, 'to_field')
        self.assertEqual(response.context['to_field'], self.to_field)
        self.assertInContext(response, 'is_popup')
        self.assertEqual(response.context['is_popup'], self.is_popup)
        self.assertInContext(response, 'to_field_var')
        self.assertEqual(response.context['to_field_var'], self.to_field_var)
        self.assertInContext(response, 'is_popup_var')
        self.assertEqual(response.context['is_popup_var'], self.is_popup_var)

    def _test_display_delete_pop_up_window_response(self):
        response = self.response

        self.assertInContext(response, 'is_popup')
        self.assertEqual(response.context['is_popup'], self.is_popup)
        self.assertInContext(response, 'is_popup_var')
        self.assertEqual(response.context['is_popup_var'], self.is_popup_var)

    def _test_pop_up_window_success_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, 'dashboard/widgets/popup_response.html')
        self.assertInContext(response, 'popup_response_data')
        self.popup_response_data = json.loads(response.context['popup_response_data'])

    def _test_create_pop_up_window_success_response(self):
        self._test_pop_up_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue('value' in popup_response_data)
        self.assertTrue('obj' in popup_response_data)
        self.assertFalse('action' in popup_response_data)

        response = self.response
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

    def _test_update_pop_up_window_success_response(self):
        self._test_pop_up_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue('action' in popup_response_data)
        self.assertEqual(popup_response_data['action'], 'change')
        self.assertTrue('value' in popup_response_data)
        self.assertTrue('obj' in popup_response_data)
        self.assertTrue('new_value' in popup_response_data)

        response = self.response
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

    def _test_delete_pop_up_window_success_response(self):
        self._test_pop_up_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue('action' in popup_response_data)
        self.assertEqual(popup_response_data['action'], 'delete')
        self.assertTrue('value' in popup_response_data)

        response = self.response
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)


class AttributeOptionGroupRegularWindowMixin(object):

    def _test_display_regular_window_response(self):
        response = self.response

        self.assertTrue('to_field' not in response.context)
        self.assertTrue('is_popup' not in response.context)
        self.assertTrue('to_field_var' not in response.context)
        self.assertTrue('is_popup_var' not in response.context)

    def _test_regular_window_success_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.FOUND)
        self.assertRedirectsTo(response, self.success_url_name)
        messages = list(response.follow().context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, INFO)
        self.assertEqual(messages[0].message, self.success_message)


class TestAttributeOptionGroupCreateView(AttributeOptionGroupCreateMixin,
                                         AttributeOptionGroupPopUpWindowMixin,
                                         AttributeOptionGroupRegularWindowMixin,
                                         WebTestCase):
    is_staff = True

    def test_display_create_form_via_popup_window(self):
        self._set_up_display_create_form_vars()
        self._set_up_pop_up_window_vars()

        url = reverse(self.url_name)
        params = {
            self.to_field_var: self.to_field,
            self.is_popup_var: self.is_popup,
        }
        querystring = urlencode(params)
        url = '%s?%s' % (url, querystring)
        self.response = self.get(url)

        # Test the response
        self._test_display_create_form_response()
        self._test_display_pop_up_window_response()

    def test_display_create_form_via_regular_window(self):
        self._set_up_display_create_form_vars()

        self.response = self.get(reverse(self.url_name))

        # Test the response
        self._test_display_create_form_response()
        self._test_display_regular_window_response()

    def test_create_via_popup_window(self):
        self._set_up_create_vars()
        self._set_up_pop_up_window_vars()

        form = self.get(reverse(self.url_name)).form
        form['name'] = self.attribute_option_group_name
        form['options-0-option'] = self.attribute_option_option
        params = dict(form.submit_fields())
        params[self.to_field_var] = self.to_field
        params[self.is_popup_var] = self.is_popup
        self.response = self.post(reverse(self.url_name), params=params)

        # Test the creation of the attribute option group and attribute option
        self._test_creation_of_objects()

        # Test the response
        self._test_create_pop_up_window_success_response()

    def test_create_via_regular_window(self):
        self._set_up_create_vars()
        self._set_up_create_success_vars()

        form = self.get(reverse(self.url_name)).form
        form['name'] = self.attribute_option_group_name
        form['options-0-option'] = self.attribute_option_option
        self.response = form.submit()

        # Test the creation of the attribute option group and attribute option
        self._test_creation_of_objects()

        # Test the response
        self._test_regular_window_success_response()


class TestAttributeOptionGroupUpdateView(AttributeOptionGroupUpdateMixin,
                                         AttributeOptionGroupPopUpWindowMixin,
                                         AttributeOptionGroupRegularWindowMixin,
                                         WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestAttributeOptionGroupUpdateView, self).setUp()

        self.attribute_option_group = AttributeOptionGroupFactory()
        AttributeOptionFactory(group=self.attribute_option_group)

    def test_display_update_form_via_popup_window(self):
        self._set_up_display_update_form_vars()
        self._set_up_pop_up_window_vars()

        params = {
            self.to_field_var: self.to_field,
            self.is_popup_var: self.is_popup,
        }
        querystring = urlencode(params)
        url = '%s?%s' % (self.url, querystring)
        self.response = self.get(url)

        # Test the response
        self._test_display_update_form_response()
        self._test_display_pop_up_window_response()

    def test_display_update_form_via_regular_window(self):
        self._set_up_display_update_form_vars()

        self.response = self.get(self.url)

        # Test the response
        self._test_display_update_form_response()
        self._test_display_regular_window_response()

    def test_update_via_popup_window(self):
        self._set_up_update_vars()
        self._set_up_pop_up_window_vars()

        form = self.get(self.url).form
        form['name'] = self.attribute_option_group_name
        form['options-0-option'] = self.attribute_option_option
        params = dict(form.submit_fields())
        params[self.to_field_var] = self.to_field
        params[self.is_popup_var] = self.is_popup
        self.response = self.post(self.url, params=params)

        # Test the update of the attribute option group and attribute option
        self._test_update_of_objects()

        # Test the response
        self._test_update_pop_up_window_success_response()

    def test_update_via_regular_window(self):
        self._set_up_update_vars()
        self._set_up_update_success_vars()

        form = self.get(self.url).form
        form['name'] = self.attribute_option_group_name
        form['options-0-option'] = self.attribute_option_option
        self.response = form.submit()

        # Test the update of the attribute option group and attribute option
        self._test_update_of_objects()

        # Test the response
        self._test_regular_window_success_response()


class TestAttributeOptionGroupListView(WebTestCase):
    is_staff = True

    def test_display_pagination_navigation(self):
        url_name = 'dashboard:catalogue-attribute-option-group-list'
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
        attribute_option_group_name = 'Test Attribute Option Group #%d'

        for i in range(0, int(1.5 * per_page)):
            AttributeOptionGroupFactory(name=attribute_option_group_name % i)

        page = self.get(reverse(url_name))

        # Test the pagination
        self.assertContains(page, 'Page 1 of 2')


class TestAttributeOptionGroupDeleteView(AttributeOptionGroupDeleteMixin,
                                         AttributeOptionGroupPopUpWindowMixin,
                                         AttributeOptionGroupRegularWindowMixin,
                                         WebTestCase):
    is_staff = True

    def setUp(self):
        super(TestAttributeOptionGroupDeleteView, self).setUp()

        self.attribute_option_group = AttributeOptionGroupFactory()
        AttributeOptionFactory(group=self.attribute_option_group)

    def test_display_delete_form_via_popup_window(self):
        self._set_up_display_delete_form_vars()
        self._set_up_display_delete_form_allowed_vars()
        self._set_up_pop_up_window_vars()

        params = {
            self.is_popup_var: self.is_popup,
        }
        querystring = urlencode(params)
        url = '%s?%s' % (self.url, querystring)
        self.response = self.get(url)

        # Test the response
        self._test_display_delete_form_response()
        self._test_display_delete_pop_up_window_response()

    def test_display_delete_disallowed_via_popup_window(self):
        self._set_up_display_delete_form_vars()
        self._set_up_display_delete_form_disallowed_vars()
        self._set_up_pop_up_window_vars()

        ProductAttributeFactory(type='multi_option', name='Sizes', code='sizes', option_group=self.attribute_option_group)

        params = {
            self.is_popup_var: self.is_popup,
        }
        querystring = urlencode(params)
        url = '%s?%s' % (self.url, querystring)
        self.response = self.get(url)

        # Test the response
        self._test_display_delete_form_response()
        self._test_display_delete_disallowed_response()
        self._test_display_delete_pop_up_window_response()

    def test_display_delete_form_via_regular_window(self):
        self._set_up_display_delete_form_vars()
        self._set_up_display_delete_form_allowed_vars()

        self.response = self.get(self.url)

        # Test the response
        self._test_display_delete_form_response()
        self._test_display_regular_window_response()

    def test_display_disallowed_delete_via_regular_window(self):
        self._set_up_display_delete_form_vars()
        self._set_up_display_delete_form_disallowed_vars()

        ProductAttributeFactory(type='multi_option', name='Sizes', code='sizes', option_group=self.attribute_option_group)

        self.response = self.get(self.url)

        # Test the response
        self._test_display_delete_form_response()
        self._test_display_delete_disallowed_response()
        self._test_display_regular_window_response()

    def test_delete_via_popup_window(self):
        self._set_up_delete_vars()
        self._set_up_pop_up_window_vars()

        form = self.get(self.url).form
        params = dict(form.submit_fields())
        params[self.is_popup_var] = self.is_popup
        self.response = self.post(self.url, params=params)

        # Test the deletion of the attribute option group and attribute option
        self._test_deletion_of_objects()

        # Test the response
        self._test_delete_pop_up_window_success_response()

    def test_delete_via_regular_window(self):
        self._set_up_delete_vars()
        self._set_up_delete_success_vars()

        form = self.get(self.url).form
        self.response = form.submit()

        # Test the deletion of the attribute option group and attribute option
        self._test_deletion_of_objects()

        # Test the response
        self._test_regular_window_success_response()
