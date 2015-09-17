from django.test import TestCase

from oscar.apps.dashboard.promotions import forms
from oscar.core.loading import get_classes

RawHTML, PagePromotion = get_classes('promotions.models', ['RawHTML', 'PagePromotion'])


class TestPagePromotionForm(TestCase):

    def test_page_promotion_has_fields(self):
        promotion = RawHTML()
        promotion.save()
        instance = PagePromotion(content_object=promotion)
        data = {'position': 'page', 'page_url': '/'}
        form = forms.PagePromotionForm(data=data, instance=instance)
        self.assertTrue(form.is_valid())
        page_promotion = form.save()
        self.assertEqual(page_promotion.page_url, '/')
