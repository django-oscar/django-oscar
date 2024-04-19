from unittest import mock

import pytest
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.urls import include, path

from oscar.apps.dashboard.nav import _dashboard_url_names_to_config
from oscar.core.application import OscarDashboardConfig


class PathAppConfig(AppConfig):
    path = "fake"


class DashConfig(OscarDashboardConfig):
    path = "fake"

    def get_urls(self):
        return [
            path("a", lambda x: x, name="lol"),
            path("b", lambda x: x),
            path(
                "c",
                include(
                    [
                        path("d", lambda x: x, name="foo"),
                    ]
                ),
            ),
        ]


def test_only_returns_dashboard_urls():
    with mock.patch("oscar.apps.dashboard.nav.apps.get_app_configs") as mock_configs:
        mock_configs.return_value = [PathAppConfig("name", "module")]
        output = _dashboard_url_names_to_config.__wrapped__()

    assert not output


def test_only_returns_named_urls_and_skips_includes():
    config = DashConfig("name", "module")
    with mock.patch("oscar.apps.dashboard.nav.apps.get_app_configs") as mock_configs:
        mock_configs.return_value = [config]
        output = _dashboard_url_names_to_config.__wrapped__()

    assert output == {"lol": config}


def test_raises_if_same_name_in_different_configs():
    config_a = DashConfig("a_name", "a_module")
    config_b = DashConfig("b_name", "b_module")
    with mock.patch("oscar.apps.dashboard.nav.apps.get_app_configs") as mock_configs:
        mock_configs.return_value = [config_a, config_b]
        with pytest.raises(ImproperlyConfigured):
            _dashboard_url_names_to_config.__wrapped__()
