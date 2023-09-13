# pylint: disable=abstract-method
import json
from http import client as http_client

from django.conf import settings
from django.contrib.messages import INFO
from django.urls import reverse
from django.utils.http import urlencode

from oscar.core.loading import get_class

RelatedFieldWidgetWrapper = get_class("dashboard.widgets", "RelatedFieldWidgetWrapper")


class ListViewMixin:
    url_name = None
    per_page = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def _create_object(self, idx):
        raise NotImplementedError

    def _get_url(self):
        return reverse(self.url_name)

    def test_display_pagination_navigation(self):
        for idx in range(0, int(1.5 * self.per_page)):
            self._create_object(idx)

        page = self.get(self._get_url())

        # Test the pagination
        self.assertContains(page, "Page 1 of 2")


class ResponseObjectMixin:
    url_name = None

    def _test_success_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.FOUND)
        self.assertRedirectsTo(response, self.success_url_name)
        messages = list(response.follow().context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, INFO)
        self.assertEqual(messages[0].message, self.success_message)

    def _get_url(self):
        raise NotImplementedError


class PopUpWindowMixin:
    is_popup_testcase = None

    @property
    def is_popup(self):
        return RelatedFieldWidgetWrapper.IS_POPUP_VALUE

    @property
    def is_popup_var(self):
        return RelatedFieldWidgetWrapper.IS_POPUP_VAR

    @property
    def to_field(self):
        return self.model._meta.pk.name

    @property
    def to_field_var(self):
        return RelatedFieldWidgetWrapper.TO_FIELD_VAR

    def _test_popup_window_success_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, "oscar/dashboard/widgets/popup_response.html")
        self.assertInContext(response, "popup_response_data")
        self.popup_response_data = json.loads(response.context["popup_response_data"])

    def _test_display_regular_window_response(self):
        response = self.response

        self.assertTrue("is_popup" not in response.context)
        self.assertTrue("is_popup_var" not in response.context)

    def _get_popup_params(self):
        return {
            self.is_popup_var: self.is_popup,
        }

    def _get_popup_url(self, url):
        querystring = urlencode(self._get_popup_params())
        return "%s?%s" % (url, querystring)


class PopUpWindowCreateUpdateMixin(PopUpWindowMixin):
    def _test_display_regular_window_response(self):
        super()._test_display_regular_window_response()
        response = self.response
        self.assertTrue("to_field" not in response.context)
        self.assertTrue("to_field_var" not in response.context)

    def _test_display_popup_window_response(self):
        response = self.response

        self.assertInContext(response, "to_field")
        self.assertEqual(response.context["to_field"], self.to_field)
        self.assertInContext(response, "is_popup")
        self.assertEqual(response.context["is_popup"], self.is_popup)
        self.assertInContext(response, "to_field_var")
        self.assertEqual(response.context["to_field_var"], self.to_field_var)
        self.assertInContext(response, "is_popup_var")
        self.assertEqual(response.context["is_popup_var"], self.is_popup_var)

    def _get_popup_params(self):
        params = super()._get_popup_params()
        params.update({self.to_field_var: self.to_field})
        return params


class ObjectCreateMixin(ResponseObjectMixin):
    model = None
    form = None
    page_title = None
    url_name = None
    template_name = None
    success_message = None
    success_url_name = None
    create_check_attr = None
    object_check_str = None

    def _get_url(self):
        return reverse(self.url_name)

    def _test_display_create_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertInContext(response, "form")
        self.assertIsInstance(response.context["form"], self.form)
        self.assertTrue(response.context["form"].instance._state.adding)
        self.assertInContext(response, "title")
        self.assertEqual(response.context["title"], self.page_title)

    def test_display_create_form(self):
        self.response = self.get(reverse(self.url_name))
        # Test the response
        self._test_display_create_form_response()

    def _test_creation_of_objects(self):
        # Test the creation of an object
        self.assertEqual(1, self.model.objects.all().count())
        self.obj = self.model.objects.first()
        self.assertEqual(
            getattr(self.obj, self.create_check_attr), self.object_check_str
        )

    def _get_create_obj_response(self):
        raise NotImplementedError

    def test_create_object(self):
        self.response = self._get_create_obj_response()
        # Test the creation of an object
        self._test_creation_of_objects()

        # Test the response
        self._test_success_response()


class PopUpObjectCreateMixin(PopUpWindowCreateUpdateMixin, ObjectCreateMixin):
    def _get_url(self):
        url = super()._get_url()
        if self.is_popup_testcase:
            return self._get_popup_url(url)
        return url

    def test_display_create_form(self):
        super().test_display_create_form()
        self._test_display_regular_window_response()

    def test_display_create_popup_form(self):
        self.is_popup_testcase = True
        self.url = self._get_url()
        self.response = self.get(self._get_url())

        # Test the response
        self._test_display_create_form_response()
        self._test_display_popup_window_response()

    def test_create_popup_object(self):
        self.is_popup_testcase = True
        self.response = self._get_create_obj_response()
        # Test the creation of an object
        self._test_creation_of_objects()
        # Test the response
        self._test_create_popup_success_response()

    def _test_create_popup_success_response(self):
        self._test_popup_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue("value" in popup_response_data)
        self.assertTrue("obj" in popup_response_data)
        self.assertFalse("action" in popup_response_data)

        response = self.response
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 0)


class ObjectUpdateMixin(ResponseObjectMixin):
    model = None
    form = None
    page_title = None
    url_name = None
    template_name = None
    success_message = None
    success_url_name = None
    create_check_attr = None
    object_check_str = None

    def _get_url(self):
        return reverse(self.url_name, kwargs={"pk": self.obj.pk})

    def _get_page_title(self):
        raise NotImplementedError

    def _create_object_factory(self):
        raise NotImplementedError

    def setUp(self):
        super().setUp()
        self.obj = self._create_object_factory()

    def _test_display_update_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertInContext(response, "form")
        self.assertIsInstance(response.context["form"], self.form)
        self.assertEqual(response.context["form"].instance, self.obj)
        self.assertInContext(response, "title")
        self.assertEqual(response.context["title"], self._get_page_title())

    def test_display_update_form(self):
        self.response = self.get(self._get_url())
        # Test the response
        self._test_display_update_form_response()

    def _test_update_of_objects(self):
        # Test the update of an object
        self.obj = self.model.objects.first()
        self.assertEqual(
            getattr(self.obj, self.create_check_attr), self.object_check_str
        )

    def _get_update_obj_response(self):
        raise NotImplementedError

    def test_update_object(self):
        self.response = self._get_update_obj_response()
        # Test the update of an object
        self._test_update_of_objects()
        # Test the response
        self._test_success_response()


class PopUpObjectUpdateMixin(PopUpWindowCreateUpdateMixin, ObjectUpdateMixin):
    def _get_url(self):
        url = super()._get_url()
        if self.is_popup_testcase:
            return self._get_popup_url(url)
        return url

    def test_display_update_form(self):
        super().test_display_update_form()
        self._test_display_regular_window_response()

    def test_display_update_popup_form(self):
        self.is_popup_testcase = True
        self.url = self._get_url()
        self.response = self.get(self._get_url())

        # Test the response
        self._test_display_update_form_response()
        self._test_display_popup_window_response()

    def test_update_popup_object(self):
        self.is_popup_testcase = True
        self.response = self._get_update_obj_response()
        # Test the creation of an object
        self._test_update_of_objects()
        # Test the response
        self._test_update_popup_success_response()

    def _test_update_popup_success_response(self):
        self._test_popup_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue("action" in popup_response_data)
        self.assertEqual(popup_response_data["action"], "change")
        self.assertTrue("value" in popup_response_data)
        self.assertTrue("obj" in popup_response_data)
        self.assertTrue("new_value" in popup_response_data)

        response = self.response
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 0)


class ObjectDeleteMixin(ResponseObjectMixin):
    model = None
    page_title = None
    url_name = None
    template_name = None
    success_message = None
    success_url_name = None
    delete_dissalowed_possible = None

    def _get_url(self):
        return reverse(self.url_name, kwargs={"pk": self.obj.pk})

    def _get_page_title(self):
        raise NotImplementedError

    def _create_object_factory(self):
        raise NotImplementedError

    def setUp(self):
        super().setUp()
        self.obj = self._create_object_factory()

    def _test_display_delete_form_response(self):
        response = self.response

        self.assertEqual(response.status_code, http_client.OK)
        self.assertTemplateUsed(response, self.template_name)
        self.assertInContext(response, "title")
        self.assertEqual(response.context["title"], self._get_page_title())

    def test_display_delete_form(self):
        self.response = self.get(self._get_url())
        # Test the response
        self._test_display_delete_form_response()

    def test_delete_object(self):
        self.response = self._get_delete_obj_response()
        # Test the deletion of an object
        self._test_deletion_of_objects()
        # Test the response
        self._test_success_response()

    def _get_delete_obj_response(self):
        raise NotImplementedError

    def _test_deletion_of_objects(self):
        # Test the deletion of an object
        obj_exists = self.model.objects.exists()
        self.assertFalse(obj_exists)

    def test_display_disallowed_delete(self):
        if self.delete_dissalowed_possible:
            self.is_disallowed_test = True
            self._create_dissalowed_object_factory()
            self.response = self.get(self._get_url())
            # Test the response
            self._test_display_delete_disallowed_response()

    def _create_dissalowed_object_factory(self):
        raise NotImplementedError

    def _test_display_delete_disallowed_response(self):
        response = self.response

        self.assertInContext(response, "disallow")
        self.assertTrue(response.context["disallow"])


class PopUpObjectDeleteMixin(PopUpWindowMixin, ObjectDeleteMixin):
    def _get_url(self):
        url = super()._get_url()
        if self.is_popup_testcase:
            return self._get_popup_url(url)
        return url

    def test_display_delete_form(self):
        super().test_display_delete_form()
        self._test_display_regular_window_response()

    def test_display_delete_popup_form(self):
        self.is_popup_testcase = True
        self.url = self._get_url()
        self.response = self.get(self._get_url())

        # Test the response
        self._test_display_delete_form_response()
        self._test_display_popup_delete_response()

    def _test_display_popup_delete_response(self):
        response = self.response

        self.assertInContext(response, "is_popup")
        self.assertEqual(response.context["is_popup"], self.is_popup)
        self.assertInContext(response, "is_popup_var")
        self.assertEqual(response.context["is_popup_var"], self.is_popup_var)

    def test_delete_popup_object(self):
        self.is_popup_testcase = True
        self.response = self._get_delete_obj_response()
        # Test the deletion of an object
        self._test_deletion_of_objects()
        # Test the response
        self._test_delete_popup_success_response()

    def _test_delete_popup_success_response(self):
        self._test_popup_window_success_response()
        popup_response_data = self.popup_response_data

        self.assertTrue("action" in popup_response_data)
        self.assertEqual(popup_response_data["action"], "delete")
        self.assertTrue("value" in popup_response_data)

        response = self.response
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 0)

    def test_display_disallowed_delete(self):
        super().test_display_disallowed_delete()
        self._test_display_regular_window_response()

    def test_display_disallowed_popup_delete(self):
        if self.delete_dissalowed_possible:
            self.is_popup_testcase = True
            self.is_disallowed_test = True
            self._create_dissalowed_object_factory()
            self.response = self.get(self._get_url())
            # Test the response
            self._test_display_popup_delete_response()
            self._test_display_delete_disallowed_response()
