from django.test import SimpleTestCase
from oscar.apps.dashboard.catalogue.forms import ProductForm, CategoryForm

class TestProductFormXSS(SimpleTestCase):
    def test_script_tag_sanitized_in_description(self):
        """Fails if clean_description() is removed from ProductForm"""
        form = ProductForm.__new__(ProductForm)
        form.cleaned_data = {"description": "<script>alert(1)</script>"}
        result = form.clean_description()
        assert "<script>" not in result

    def test_safe_html_allowed_in_description(self):
        """Safe HTML must survive sanitization"""
        form = ProductForm.__new__(ProductForm)
        form.cleaned_data = {"description": "<p><b>Bold</b></p>"}
        result = form.clean_description()
        assert "<p>" in result

class TestCategoryFormXSS(SimpleTestCase):
    def test_script_tag_sanitized_in_description(self):
        """Fails if clean_description() is removed from CategoryForm"""
        form = CategoryForm.__new__(CategoryForm)
        form.cleaned_data = {"description": "<script>alert(1)</script>"}
        result = form.clean_description()
        assert "<script>" not in result