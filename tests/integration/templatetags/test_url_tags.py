from django import template
from django.contrib.sites.models import Site
from django.test import TestCase


class TestUrlTags(TestCase):
    def test_absolute_url_tag(self):
        tmpl = template.Template(
            "{% load i18n %}"
            "{% load url_tags %}"
            "{% absolute_url site.domain path %}."
        )
        out = tmpl.render(
            template.Context(
                {
                    "site": Site.objects.get_current(),
                    "path": "/some/test/path",
                }
            )
        )
        assert out == "http://example.com/some/test/path."

    def test_absolute_url_tag_with_blocktrans(self):
        tmpl = template.Template(
            "{% load i18n %}"
            "{% load url_tags %}"
            "{% absolute_url site.domain path_1 as url_1 %}"
            "{% absolute_url site.domain path_2 as url_2 %}"
            "{% blocktrans with test_url_1=url_1 test_url_2=url_2 %}"
            "1st - {{ test_url_1 }}. 2nd - {{ test_url_2 }}."
            "{% endblocktrans %}"
        )
        out = tmpl.render(
            template.Context(
                {
                    "site": Site.objects.get_current(),
                    "path_1": "/some/test/path",
                    "path_2": "/some/another/test/path",
                }
            )
        )
        assert (
            out
            == "1st - http://example.com/some/test/path. 2nd - http://example.com/some/another/test/path."
        )
