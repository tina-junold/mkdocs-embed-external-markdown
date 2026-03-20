import os
from unittest.mock import patch

import pytest

from external_markdown.plugin import EmbedExternalMarkdown

BASE_URL = "https://BASEURL/"
BASE_FILE = "https://BASEURL/FILE.md"
TEST_DATA = [
    (
        "external link",
        "https://github.com",
        "https://github.com"),
    (
        "external link with anchor",
        "https://ansible-docs.readthedocs.io/zh/stable-2.0/rst/playbooks_variables.html#using-variables-about-jinja2",
        "https://ansible-docs.readthedocs.io/zh/stable-2.0/rst/playbooks_variables.html#using-variables-about-jinja2",
    ),
    (
        "anchor",
        "#links",
        "#links"),
    (
        "local link",
        "page.md",
        f"{BASE_URL}page.md"),
    (
        "local link with anchor",
        "page.md#test-subsection",
        f"{BASE_URL}page.md#test-subsection",
    ),
]


class TestEmbedExternalMarkdown:
    @pytest.mark.parametrize("label,link_url,expected_url", TEST_DATA)
    def test_update_relative_links_external(self, label, link_url, expected_url):
        # Regression tests for #11
        link = f"[{label}]({link_url})"
        expected = f"[{label}]({expected_url})"
        assert EmbedExternalMarkdown().update_relative_links(link, BASE_FILE) == expected

    def _plugin_with_config(self, **config_overrides):
        plugin = EmbedExternalMarkdown()
        plugin.config = {"gitlab_token": "", "gitlab_hostnames": ["gitlab.com"], **config_overrides}
        return plugin

    @patch("external_markdown.plugin.get")
    def test_make_request_gitlab_token_from_env(self, mock_get):
        plugin = self._plugin_with_config()
        with patch.dict(os.environ, {"GL_TOKEN": "env-gl-token"}, clear=False):
            plugin.make_request("https://gitlab.com/group/repo/-/raw/main/README.md")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"].get("PRIVATE-TOKEN") == "env-gl-token"

    @patch("external_markdown.plugin.get")
    def test_make_request_gitlab_token_from_config(self, mock_get):
        plugin = self._plugin_with_config(gitlab_token="cfg-gl-token")
        plugin.make_request("https://gitlab.com/group/repo/-/raw/main/README.md")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"].get("PRIVATE-TOKEN") == "cfg-gl-token"

    @patch("external_markdown.plugin.get")
    def test_make_request_gitlab_custom_hostname(self, mock_get):
        plugin = self._plugin_with_config(
            gitlab_token="cfg-gl-token",
            gitlab_hostnames=["gitlab.com", "git.example.com"],
        )
        plugin.make_request("https://git.example.com/group/repo/-/raw/main/README.md")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"].get("PRIVATE-TOKEN") == "cfg-gl-token"

    @patch("external_markdown.plugin.get")
    def test_make_request_gitlab_token_not_added_for_non_gitlab_host(self, mock_get):
        plugin = self._plugin_with_config(gitlab_token="cfg-gl-token")
        plugin.make_request("https://raw.githubusercontent.com/org/repo/main/README.md")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert "PRIVATE-TOKEN" not in kwargs["headers"]

    @patch("external_markdown.plugin.get")
    def test_make_request_no_gitlab_token(self, mock_get):
        plugin = self._plugin_with_config()
        with patch.dict(os.environ, {}, clear=True):
            plugin.make_request("https://gitlab.com/group/repo/-/raw/main/README.md")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert "PRIVATE-TOKEN" not in kwargs["headers"]
