from django.contrib.messages import ERROR
from django.utils.translation import gettext

from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    AttributeOptionFactory,
    AttributeOptionGroupFactory,
    ProductAttributeFactory,
)
from oscar.test.testcases import WebTestCase

from .testcases import (
    ListViewMixin,
    PopUpObjectCreateMixin,
    PopUpObjectDeleteMixin,
    PopUpObjectUpdateMixin,
)

AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")

AttributeOptionGroupForm = get_class(
    "dashboard.catalogue.forms", "AttributeOptionGroupForm"
)
AttributeOptionFormSet = get_class(
    "dashboard.catalogue.formsets", "AttributeOptionFormSet"
)


class TestAttributeOptionGroupListView(ListViewMixin, WebTestCase):
    is_staff = True
    url_name = "dashboard:catalogue-attribute-option-group-list"

    def _create_object(self, idx):
        attribute_option_group_name = "Test Attribute Option Group #%d"
        AttributeOptionGroupFactory(name=attribute_option_group_name % idx)


class TestAttributeOptionGroupCreateView(PopUpObjectCreateMixin, WebTestCase):
    is_staff = True
    model = AttributeOptionGroup
    form = AttributeOptionGroupForm
    page_title = gettext("Add a new Attribute Option Group")
    url_name = "dashboard:catalogue-attribute-option-group-create"
    template_name = "oscar/dashboard/catalogue/attribute_option_group_form.html"
    success_message = gettext("Attribute Option Group created successfully")
    success_url_name = "dashboard:catalogue-attribute-option-group-list"
    create_check_attr = "name"
    object_check_str = "Test Attribute Option"
    attribute_option_option = "Test Attribute Option Group"

    def _test_display_create_form_response(self):
        super()._test_display_create_form_response()
        response = self.response
        self.assertInContext(response, "attribute_option_formset")
        self.assertIsInstance(
            response.context["attribute_option_formset"], AttributeOptionFormSet
        )
        self.assertTrue(
            response.context["attribute_option_formset"].instance._state.adding
        )

    def _test_creation_of_objects(self):
        super()._test_creation_of_objects()
        # Test the creation of the attribute option
        self.assertEqual(1, AttributeOption.objects.all().count())
        attribute_option = AttributeOption.objects.first()
        self.assertEqual(attribute_option.group, self.obj)
        self.assertEqual(attribute_option.option, self.attribute_option_option)

    def _get_create_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        form["options-0-option"] = self.attribute_option_option
        return form.submit()


class TestAttributeOptionGroupUpdateView(PopUpObjectUpdateMixin, WebTestCase):
    is_staff = True
    model = AttributeOptionGroup
    form = AttributeOptionGroupForm
    page_title = None
    url_name = "dashboard:catalogue-attribute-option-group-update"
    template_name = "oscar/dashboard/catalogue/attribute_option_group_form.html"
    success_message = gettext("Attribute Option Group updated successfully")
    success_url_name = "dashboard:catalogue-attribute-option-group-list"
    create_check_attr = "name"
    object_check_str = "Test Attribute Option"
    attribute_option_option = "Test Attribute Option Group"

    def _create_object_factory(self):
        obj = AttributeOptionGroupFactory()
        AttributeOptionFactory(group=obj)
        return obj

    def _get_page_title(self):
        return gettext("Update Attribute Option Group '%s'") % self.obj.name

    def _get_update_obj_response(self):
        form = self.get(self._get_url()).form
        form["name"] = self.object_check_str
        form["options-0-option"] = self.attribute_option_option
        return form.submit()

    def _test_display_update_form_response(self):
        super()._test_display_update_form_response()
        response = self.response

        self.assertInContext(response, "attribute_option_formset")
        self.assertIsInstance(
            response.context["attribute_option_formset"], AttributeOptionFormSet
        )
        self.assertEqual(
            response.context["attribute_option_formset"].initial_forms[0].instance,
            self.obj.options.first(),
        )

    def _test_update_of_objects(self):
        super()._test_update_of_objects()
        # Test the update of the attribute option
        self.assertEqual(self.obj.options.first().option, self.attribute_option_option)


class TestAttributeOptionGroupDeleteView(PopUpObjectDeleteMixin, WebTestCase):
    is_staff = True
    model = AttributeOptionGroup
    page_title = None
    url_name = "dashboard:catalogue-attribute-option-group-delete"
    template_name = "oscar/dashboard/catalogue/attribute_option_group_delete.html"
    success_message = gettext("Attribute Option Group deleted successfully")
    success_url_name = "dashboard:catalogue-attribute-option-group-list"
    delete_dissalowed_possible = True

    def _create_object_factory(self):
        obj = AttributeOptionGroupFactory()
        AttributeOptionFactory(group=obj)
        return obj

    def _get_page_title(self):
        if getattr(self, "is_disallowed_test", None):
            return gettext("Unable to delete '%s'") % self.obj.name
        return gettext("Delete Attribute Option Group '%s'") % self.obj.name

    def _get_delete_obj_response(self):
        form = self.get(self._get_url()).form
        return form.submit()

    def _create_dissalowed_object_factory(self):
        ProductAttributeFactory(
            type="multi_option", name="Sizes", code="sizes", option_group=self.obj
        )

    def _test_deletion_of_objects(self):
        super()._test_deletion_of_objects()

        # Test the deletion of the attribute option
        attribute_option_exists = AttributeOption.objects.exists()
        self.assertFalse(attribute_option_exists)

    def _test_display_delete_disallowed_response(self):
        super()._test_display_delete_disallowed_response()
        response = self.response
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, ERROR)
        self.assertEqual(
            messages[0].message,
            gettext(
                "1 product attributes are still assigned to this attribute option group"
            ),
        )
