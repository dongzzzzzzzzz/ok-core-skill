"""get_client() order: Bridge -> CDP -> Playwright"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import ok.client.factory as factory
import pytest
from ok.client.cdp_client import CdpConnectionError


@pytest.fixture(autouse=True)
def _reset_singleton():
    factory._client_instance = None
    yield
    factory._client_instance = None


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_prefers_bridge_when_ping_succeeds(mock_bridge_cls, _mock_cdp, _mock_pw):
    mock_bridge = MagicMock()
    mock_bridge.ping.return_value = True
    mock_bridge_cls.return_value = mock_bridge

    client = factory.get_client()
    assert client is mock_bridge
    mock_bridge_cls.assert_called_once()
    _mock_cdp.assert_not_called()
    _mock_pw.assert_not_called()


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_cdp_when_bridge_fails_and_ok_cdp_url_set(
    mock_bridge_cls, mock_cdp_cls, _mock_pw, monkeypatch
):
    monkeypatch.setenv("OK_CDP_URL", "http://127.0.0.1:9222")

    mock_bridge = MagicMock()
    mock_bridge.ping.return_value = False
    mock_bridge_cls.return_value = mock_bridge

    mock_cdp = MagicMock()
    mock_cdp_cls.return_value = mock_cdp

    client = factory.get_client()
    assert client is mock_cdp
    mock_cdp_cls.assert_called_once()
    _mock_pw.assert_not_called()


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_playwright_fallback_when_no_cdp_env(
    mock_bridge_cls, mock_cdp_cls, mock_pw_cls, monkeypatch
):
    monkeypatch.delenv("OK_CDP_URL", raising=False)

    mock_bridge = MagicMock()
    mock_bridge.ping.return_value = False
    mock_bridge_cls.return_value = mock_bridge

    mock_pw = MagicMock()
    mock_pw_cls.return_value = mock_pw

    client = factory.get_client()
    assert client is mock_pw
    mock_cdp_cls.assert_not_called()
    mock_pw_cls.assert_called_once()


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_cdp_strict_raises_on_connection_error(
    mock_bridge_cls, mock_cdp_cls, _mock_pw, monkeypatch
):
    monkeypatch.setenv("OK_CDP_URL", "http://127.0.0.1:9222")
    monkeypatch.setenv("OK_CDP_STRICT", "1")

    mock_bridge = MagicMock()
    mock_bridge.ping.return_value = False
    mock_bridge_cls.return_value = mock_bridge

    mock_cdp_cls.side_effect = CdpConnectionError("refused")

    with pytest.raises(CdpConnectionError):
        factory.get_client()


@patch("ok.client.playwright_client.PlaywrightClient")
@patch("ok.client.factory.CdpClient")
@patch("ok.client.factory.BridgeClient")
def test_cdp_failure_falls_back_to_playwright_when_not_strict(
    mock_bridge_cls, mock_cdp_cls, mock_pw_cls, monkeypatch
):
    monkeypatch.setenv("OK_CDP_URL", "http://127.0.0.1:9222")
    monkeypatch.delenv("OK_CDP_STRICT", raising=False)

    mock_bridge = MagicMock()
    mock_bridge.ping.return_value = False
    mock_bridge_cls.return_value = mock_bridge

    mock_cdp_cls.side_effect = CdpConnectionError("refused")

    mock_pw = MagicMock()
    mock_pw_cls.return_value = mock_pw

    client = factory.get_client()
    assert client is mock_pw
    mock_pw_cls.assert_called_once()
