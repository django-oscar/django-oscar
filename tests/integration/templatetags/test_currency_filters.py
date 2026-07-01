# -*- coding: utf-8 -*-
from decimal import Decimal as D

from django import template
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import translation


def render(template_string, ctx):
    tpl = template.Template(template_string)
    return tpl.render(template.Context(ctx))


class TestCurrencyFilter(TestCase):
    def setUp(self):
        self.template = template.Template(
            "{% load currency_filters %} {{ price|currency }}"
        )

    def test_renders_price_correctly(self):
        out = self.template.render(
            template.Context(
                {
                    "price": D("10.23"),
                }
            )
        )
        self.assertTrue("£10.23" in out)

    def test_handles_none_price_gracefully(self):
        self.template.render(template.Context({"price": None}))

    def test_handles_string_price_gracefully(self):
        self.template.render(template.Context({"price": ""}))

    def test_handles_no_translation(self):
        with translation.override(None, deactivate=True):
            self.template.render(
                template.Context(
                    {
                        "price": D("10.23"),
                    }
                )
            )

    @override_settings(
        OSCAR_CURRENCY_FORMAT={
            "AUD": {
                "currency_digits": False,
                "format_type": "accounting",
            },
            "USD": {"format": "$#,##"},
            "EUR": {"currency_digits": True, "format": "#,## \u20ac"},
        }
    )
    def test_formatting_settings(self):
        template1 = template.Template(
            "{% load currency_filters %}{{ price|currency:'AUD' }}"
        )
        out1 = template1.render(
            template.Context(
                {
                    "price": D("10.23"),
                }
            )
        )
        self.assertEqual(out1, "A$10.23")
        template2 = template.Template(
            "{% load currency_filters %}{{ price|currency:'USD' }}"
        )
        out2 = template2.render(
            template.Context(
                {
                    "price": D("10.23"),
                }
            )
        )
        self.assertEqual(out2, "$10.23")
        template3 = template.Template(
            "{% load currency_filters %}{{ price|currency:'EUR' }}"
        )
        out3 = template3.render(
            template.Context(
                {
                    "price": D("10.23"),
                }
            )
        )
        self.assertEqual(out3, "10.23 €")
