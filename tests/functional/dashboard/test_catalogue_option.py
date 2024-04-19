from django.contrib.messages import ERROR
from django.utils.text import slugify
from django.utils.translation import gettext

from oscar.core.loading import get_class, get_model
from oscar.test.factories import OptionFactory, ProductClassFactory, create_product
from oscar.test.testcases import WebTestCase

from .testcases import (
    ListViewMixin,
    PopUpObjectCreateMixin,
    PopUpObjectDeleteMixin,
    PopUpObjectUpdateMixin,
)

Option = get_model("catalogue", "Option")
OptionForm = get_class("dashboard.catalogue.forms", "OptionForm")


class TestOptionListView(ListViewMixin, WebTestCase):
    is_staff = True
    url_name = "dashboard:catalogue-option-list"

    def _create_object(self, idx):
        option_name = "Test Option #%d"
        name = option_name % idx
        OptionFactory(name=name, code=slugify(name))


class TestOptionCreateView(PopUpObjectCreateMixin, WebTestCase):
    is_staff = True
    model = Option
    form = OptionForm
    page_title = gettext("Add a new Option")
    url_name = "dashboard:catalogue-option-create"
    template_name = "oscar/dashboard/catalogue/option_form.html"
    success_message = gettext("Option created successfully")
    success_url_name = "dashboard:catalogue-option-list"
    create_check_attr = "name"
    object_check_str = "Test Option"

    def _get_create_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        return form.submit()


class TestOptionUpdateView(PopUpObjectUpdateMixin, WebTestCase):
    is_staff = True
    model = Option
    form = OptionForm
    page_title = None
    url_name = "dashboard:catalogue-option-update"
    template_name = "oscar/dashboard/catalogue/option_form.html"
    success_message = gettext("Option updated successfully")
    success_url_name = "dashboard:catalogue-option-list"
    create_check_attr = "name"
    object_check_str = "Test Option"

    def _create_object_factory(self):
        return OptionFactory()

    def _get_page_title(self):
        return gettext("Update Option '%s'") % self.obj.name

    def _get_update_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        return form.submit()


class TestOptionDeleteView(PopUpObjectDeleteMixin, WebTestCase):
    is_staff = True
    model = Option
    page_title = None
    url_name = "dashboard:catalogue-option-delete"
    template_name = "oscar/dashboard/catalogue/option_delete.html"
    success_message = gettext("Option deleted successfully")
    success_url_name = "dashboard:catalogue-option-list"
    delete_dissalowed_possible = True

    def _create_object_factory(self):
        return OptionFactory()

    def _get_page_title(self):
        if getattr(self, "is_disallowed_test", None):
            return gettext("Unable to delete '%s'") % self.obj.name
        return gettext("Delete Option '%s'") % self.obj.name

    def _get_delete_obj_response(self):
        form = self.get(self._get_url()).form
        return form.submit()

    def _create_dissalowed_object_factory(self):
        product_class = ProductClassFactory()
        product = create_product(product_class=product_class)
        product_class.options.add(self.obj)
        product.product_options.add(self.obj)

    def _test_display_delete_disallowed_response(self):
        super()._test_display_delete_disallowed_response()
        response = self.response
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(messages[1].level, ERROR)
        self.assertEqual(
            messages[0].message, "1 products are still assigned to this option"
        )
        self.assertEqual(
            messages[1].message, "1 product classes are still assigned to this option"
        )
