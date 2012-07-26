import mock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.template import Template, TemplateSyntaxError

from oscar.test import ClientTestCase
from oscar.apps.promotions import models


class PromotionTest(TestCase):

    def test_default_template_name(self):
        promotion = models.Image.objects.create(name="dummy banner")
        self.assertEqual('promotions/image.html', promotion.template_name())


class PromotionTemplateTagTest(ClientTestCase):
    anonymous = True

    def test_promotion_templatetag_argument_error(self):
        self.assertRaises(
            TemplateSyntaxError, Template,
            '{% load promotion_tags %}{% render_promotion %}',
        )

    def test_promotion_templatetag(self):
        response = self.client.get(reverse('catalogue:index'))
        promotion = models.Image.objects.create(name="dummy banner")

        template = Template(
            '{% load promotion_tags %}'
            '{% render_promotion promotion %}'
        )
        ctx = response.context[0]
        ctx.update({
            "promotion": promotion,
            "basket": mock.Mock('FakeBasket')
        })
        template.render(ctx)
        self.assertTrue('promotion' in ctx)
        self.assertTrue('basket' in ctx)
