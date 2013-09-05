# -*- coding: utf-8 -*-
from decimal import Decimal as D

from django.test import TestCase
from django import template


def render(template_string, ctx):
    tpl = template.Template(template_string)
    return tpl.render(template.Context(ctx))


class TestCurrencyFilter(TestCase):

    def setUp(self):
        self.template = template.Template(
            "{% load currency_filters %}"
            "{{ price|currency }}"
        )

    def test_renders_price_correctly(self):
        out = self.template.render(template.Context({
            'price': D('10.23'),
        }))
        self.assertTrue(u'£10.23' in out)

    def test_handles_none_price_gracefully(self):
        self.template.render(template.Context({
            'price': None
        }))

    def test_handles_string_price_gracefully(self):
        self.template.render(template.Context({
            'price': ''
        }))


class TestCurrencyTag(TestCase):

    def test_renders_uk_price_correctly(self):
        ctx = {'price': D('10.23')}
        out = render("{% load currency_tags %}{% currency price 'GBP' %}", ctx)
        self.assertTrue(u'£10.23' in out)

    def test_renders_us_price_correctly(self):
        ctx = {
            'price': D('10.23'),
            'currency': 'USD'
        }
        out = render(
            "{% load currency_tags %}{% currency price currency %}", ctx)
        self.assertTrue(u'$10.23' in out)

    def test_uses_default_currency(self):
        ctx = {'price': D('10.23')}
        out = render(
            "{% load currency_tags %}{% currency price currency %}", ctx)
        self.assertTrue(u'£10.23' in out)
