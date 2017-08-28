import json

from django.conf import settings
from django.contrib.messages import ERROR, INFO
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.six.moves import http_client
from django.utils.translation import ugettext

from oscar.apps.catalogue.models import Category
from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    AttributeOptionFactory, AttributeOptionGroupFactory,
    ProductAttributeFactory, create_product)
from oscar.test.testcases import WebTestCase

AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
AttributeOption = get_model('catalogue', 'AttributeOption')

AttributeOptionGroupForm = get_class('dashboard.catalogue.forms',
                                     'AttributeOptionGroupForm')
AttributeOptionFormSet = get_class('dashboard.catalogue.formsets',
                                   'AttributeOptionFormSet')
RelatedFieldWidgetWrapper = get_class('dashboard.catalogue.widgets',
                                      'RelatedFieldWidgetWrapper')


class TestProductDetailView(WebTestCase):

    def test_enforces_canonical_url(self):
        p = create_product()
        kwargs = {'product_slug': '1_wrong-but-valid-slug_1',
                  'pk': p.id}
        wrong_url = reverse('catalogue:detail', kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(p.get_absolute_url() in response.location)

    def test_child_to_parent_redirect(self):
        parent_product = create_product(structure='parent')
        kwargs = {'product_slug': parent_product.slug,
                  'pk': parent_product.id}
        parent_product_url = reverse('catalogue:detail', kwargs=kwargs)

        child = create_product(
            title="Variant 1", structure='child', parent=parent_product)
        kwargs = {'product_slug': child.slug,
                  'pk': child.id}
        child_url = reverse('catalogue:detail', kwargs=kwargs)

        response = self.app.get(parent_product_url)
        self.assertEqual(http_client.OK, response.status_code)

        response = self.app.get(child_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)


class TestProductListView(WebTestCase):

    def test_shows_add_to_basket_button_for_available_product(self):
        product = create_product(num_in_stock=1)
        page = self.app.get(reverse('catalogue:index'))
        self.assertContains(page, product.title)
        self.assertContains(page, ugettext("Add to basket"))

    def test_shows_not_available_for_out_of_stock_product(self):
        product = create_product(num_in_stock=0)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, product.title)
        self.assertContains(page, "Unavailable")

    def test_shows_pagination_navigation_for_multiple_pages(self):
        per_page = settings.OSCAR_PRODUCTS_PER_PAGE
        title = u"Product #%d"
        for idx in range(0, int(1.5 * per_page)):
            create_product(title=title % idx)

        page = self.app.get(reverse('catalogue:index'))

        self.assertContains(page, "Page 1 of 2")


class TestProductCategoryView(WebTestCase):

    def setUp(self):
        self.category = Category.add_root(name="Products")

    def test_browsing_works(self):
        correct_url = self.category.get_absolute_url()
        response = self.app.get(correct_url)
        self.assertEqual(http_client.OK, response.status_code)

    def test_enforces_canonical_url(self):
        kwargs = {'category_slug': '1_wrong-but-valid-slug_1',
                  'pk': self.category.pk}
        wrong_url = reverse('catalogue:category', kwargs=kwargs)

        response = self.app.get(wrong_url)
        self.assertEqual(http_client.MOVED_PERMANENTLY, response.status_code)
        self.assertTrue(self.category.get_absolute_url() in response.location)

    def test_can_chop_off_last_part_of_url(self):
        # We cache category URLs, which normally is a safe thing to do, as
        # the primary key stays the same and ProductCategoryView only looks
        # at the key any way.
        # But this test chops the URLs, and hence relies on the URLs being
        # correct. So in this case, we start with a clean cache to ensure
        # our URLs are correct.
        cache.clear()

        child_category = self.category.add_child(name='Cool products')
        full_url = child_category.get_absolute_url()
        chopped_url = full_url.rsplit('/', 2)[0]
        parent_url = self.category.get_absolute_url()
        response = self.app.get(chopped_url).follow()  # fails if no redirect
        self.assertTrue(response.url.endswith(parent_url))


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
        self.assertTemplateUsed(response, 'dashboard/catalogue/popup_response.html')
        self.assertInContext(response, 'popup_response_data')
        self.popup_response_data = json.loads(response.context['popup_response_data'])

    def _test_create_pop_up_window_success_response(self):
        self._test_pop_up_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue('value' in popup_response_data)
        self.assertTrue('obj' in popup_response_data)
        self.assertFalse('action' in popup_response_data)

    def _test_update_pop_up_window_success_response(self):
        self._test_pop_up_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue('action' in popup_response_data)
        self.assertEqual(popup_response_data['action'], 'change')
        self.assertTrue('value' in popup_response_data)
        self.assertTrue('obj' in popup_response_data)
        self.assertTrue('new_value' in popup_response_data)

    def _test_delete_pop_up_window_success_response(self):
        self._test_pop_up_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue('action' in popup_response_data)
        self.assertEqual(popup_response_data['action'], 'delete')
        self.assertTrue('value' in popup_response_data)


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
