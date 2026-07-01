# -*- coding: utf-8 -*-
from datetime import timedelta

from django import template
from django.test import TestCase
from django.utils.translation import activate


class TestDatetimeFilter(TestCase):
    def test_timedelta(self):
        activate("en-gb")
        timedelta_template = template.Template(
            "{% load datetime_filters %} {{ timedelta|timedelta }}"
        )
        out = timedelta_template.render(
            template.Context(
                {
                    "timedelta": timedelta(minutes=10),
                }
            )
        )
        self.assertTrue("10 minutes" in out)
        out = timedelta_template.render(
            template.Context(
                {
                    "timedelta": timedelta(hours=50),
                }
            )
        )
        self.assertTrue("2 days" in out)
