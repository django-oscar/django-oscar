from http import client as http_client

from django.conf import settings
from django.contrib.messages import ERROR, INFO
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext

from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    OptionFactory, ProductClassFactory, create_product)
from oscar.test.testcases import WebTestCase


Option = get_model('catalogue', 'Option')
OptionForm = get_class('dashboard.catalogue.forms', 'OptionForm')


class OptionCreateMixin(object):

    def _set_up_display_create_form_vars(self):
        self.url_name = 'dashboard:catalogue-option-create'
        self.title = gettext("Add a new Option")

    def _test_display_create_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, 'dashboard/catalogue/option_form.html')
        self.assertInContext(response, 'form')
        self.assertIsInstance(response.context['form'], OptionForm)
        self.assertTrue(response.context['form'].instance._state.adding)
        self.assertInContext(response, 'title')
        self.assertEqual(response.context['title'], self.title)

    def _set_up_create_vars(self):
        self.url_name = 'dashboard:catalogue-option-create'
        self.option_name = 'Test Option'

    def _set_up_create_success_vars(self):
        self.success_url_name = 'dashboard:catalogue-option-list'
        self.success_message = gettext("Option created successfully")

    def _test_creation_of_objects(self):
        # Test the creation of the option
        self.assertEqual(1, Option.objects.all().count())
        option = Option.objects.first()
        self.assertEqual(option.name, self.option_name)


class OptionUpdateMixin(object):

    def _set_up_display_update_form_vars(self):
        url_name = 'dashboard:catalogue-option-update'
        self.url = reverse(url_name, kwargs={'pk': self.option.pk})
        self.title = gettext("Update Option '%s'") % self.option.name

    def _test_display_update_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, 'dashboard/catalogue/option_form.html')
        self.assertInContext(response, 'form')
        self.assertIsInstance(response.context['form'], OptionForm)
        self.assertEqual(response.context['form'].instance, self.option)
        self.assertInContext(response, 'title')
        self.assertEqual(response.context['title'], self.title)

    def _set_up_update_vars(self):
        url_name = 'dashboard:catalogue-option-update'
        self.url = reverse(url_name, kwargs={'pk': self.option.pk})
        self.option_name = 'Test Option'

    def _set_up_update_success_vars(self):
        self.success_url_name = 'dashboard:catalogue-option-list'
        self.success_message = gettext("Option updated successfully")

    def _test_update_of_objects(self):
        # Test the update of the option
        option = Option.objects.first()
        self.assertEqual(option.name, self.option_name)


class OptionDeleteMixin(object):

    def _set_up_display_delete_form_vars(self):
        url_name = 'dashboard:catalogue-option-delete'
        self.url = reverse(url_name, kwargs={'pk': self.option.pk})

    def _set_up_display_delete_form_allowed_vars(self):
        self.title = gettext("Delete Option '%s'") % self.option.name

    def _set_up_display_delete_form_disallowed_objects(self):
        product_class = ProductClassFactory()
        product = create_product(product_class=product_class)
        product_class.options.add(self.option)
        product.product_options.add(self.option)

    def _set_up_display_delete_form_disallowed_vars(self):
        self.title = gettext("Unable to delete '%s'") % self.option.name
        self.error_product_message = gettext("1 products are still assigned to this option")
        self.error_class_message = gettext("1 product classes are still assigned to this option")

    def _test_display_delete_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, 'dashboard/catalogue/option_delete.html')
        self.assertInContext(response, 'title')
        self.assertEqual(response.context['title'], self.title)

    def _test_display_delete_disallowed_response(self):
        response = self.response

        self.assertInContext(response, 'disallow')
        self.assertTrue(response.context['disallow'])
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(messages[1].level, ERROR)
        self.assertEqual(messages[0].message, self.error_product_message)
        self.assertEqual(messages[1].message, self.error_class_message)

    def _set_up_delete_vars(self):
        url_name = 'dashboard:catalogue-option-delete'
        self.url = reverse(url_name, kwargs={'pk': self.option.pk})

    def _set_up_delete_success_vars(self):
        self.success_url_name = 'dashboard:catalogue-option-list'
        self.success_message = gettext("Option deleted successfully")

    def _test_deletion_of_objects(self):
        # Test the deletion of the option
        option_exists = Option.objects.exists()
        self.assertFalse(option_exists)


class TestResponseOptionMixin(object):

    def _test_success_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.FOUND)
        self.assertRedirectsTo(response, self.success_url_name)
        messages = list(response.follow().context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, INFO)
        self.assertEqual(messages[0].message, self.success_message)


class TestOptionCreateView(OptionCreateMixin,
                           TestResponseOptionMixin,
                           WebTestCase):
    is_staff = True

    def test_display_create_form(self):
        self._set_up_display_create_form_vars()

        self.response = self.get(reverse(self.url_name))

        # Test the response
        self._test_display_create_form_response()

    def test_create_option(self):
        self._set_up_create_vars()
        self._set_up_create_success_vars()

        form = self.get(reverse(self.url_name)).form
        form['name'] = self.option_name
        self.response = form.submit()

        # Test the creation of the option
        self._test_creation_of_objects()

        # Test the response
        self._test_success_response()


class TestOptionUpdateView(OptionUpdateMixin,
                           TestResponseOptionMixin,
                           WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()

        self.option = OptionFactory()

    def test_display_update_form(self):
        self._set_up_display_update_form_vars()

        self.response = self.get(self.url)

        # Test the response
        self._test_display_update_form_response()

    def test_update_option(self):
        self._set_up_update_vars()
        self._set_up_update_success_vars()

        form = self.get(self.url).form
        form['name'] = self.option_name
        self.response = form.submit()

        # Test the update of the attribute option
        self._test_update_of_objects()

        # Test the response
        self._test_success_response()


class TestOptionListView(WebTestCase):
    is_staff = True

    def test_display_pagination_navigation(self):
        url_name = 'dashboard:catalogue-option-list'
        per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
        option_name = 'Test Option #%d'

        for i in range(0, int(1.5 * per_page)):
            name = option_name % i
            OptionFactory(name=name, code=slugify(name))

        page = self.get(reverse(url_name))

        # Test the pagination
        self.assertContains(page, 'Page 1 of 2')


class TestOptionDeleteView(OptionDeleteMixin,
                           TestResponseOptionMixin,
                           WebTestCase):
    is_staff = True

    def setUp(self):
        super().setUp()

        self.option = OptionFactory()

    def test_display_delete_form(self):
        self._set_up_display_delete_form_vars()
        self._set_up_display_delete_form_allowed_vars()

        self.response = self.get(self.url)

        # Test the response
        self._test_display_delete_form_response()

    def test_display_disallowed_delete_via_regular_window(self):
        self._set_up_display_delete_form_vars()
        self._set_up_display_delete_form_disallowed_vars()
        self._set_up_display_delete_form_disallowed_objects()

        self.response = self.get(self.url)

        # Test the response
        self._test_display_delete_form_response()
        self._test_display_delete_disallowed_response()

    def test_delete_option(self):
        self._set_up_delete_vars()
        self._set_up_delete_success_vars()

        form = self.get(self.url).form
        self.response = form.submit()

        # Test the deletion of the option
        self._test_deletion_of_objects()

        # Test the response
        self._test_success_response()
