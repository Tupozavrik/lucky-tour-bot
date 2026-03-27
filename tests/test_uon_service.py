"""Тесты для UonService: нормализация стран и mock-поведение."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientError

from services.uon_service import UonService, normalize_country, _mock_destination, UonApiError


class TestNormalizeCountry:
    """Тесты функции нормализации названий стран."""

    def test_turkish_in_russian(self):
        assert normalize_country("Турция") == "Turkey"

    def test_turkish_in_english(self):
        assert normalize_country("turkey") == "Turkey"

    def test_turkish_mixed_case(self):
        assert normalize_country("TURKEY") == "Turkey"

    def test_egypt_in_russian(self):
        assert normalize_country("Египет") == "Egypt"

    def test_egypt_in_english(self):
        assert normalize_country("Egypt") == "Egypt"

    def test_unknown_country_returns_none(self):
        assert normalize_country("Марс") is None

    def test_none_input_returns_none(self):
        assert normalize_country(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_country("") is None

    def test_strips_whitespace(self):
        assert normalize_country("  Турция  ") == "Turkey"


class TestMockDestination:
    """Тесты mock-поведения при отсутствии API-ключа."""

    def test_id_123_returns_egypt(self):
        assert _mock_destination("123") == "Egypt"

    def test_any_digit_returns_turkey(self):
        assert _mock_destination("456") == "Turkey"
        assert _mock_destination("1") == "Turkey"

    def test_non_digit_returns_none(self):
        assert _mock_destination("abc") is None

    def test_empty_string_returns_none(self):
        assert _mock_destination("") is None


class TestUonServiceGetUserDestination:
    """Тесты UonService.get_user_destination с мокнутым API-ключом."""

    @pytest.mark.asyncio
    async def test_returns_turkey_when_no_api_key(self):
        """При отсутствии API-ключа должна вернуться mock-страна."""
        with patch("services.uon_service.UON_API_KEY", ""):
            result = await UonService.get_user_destination("999")
            assert result == "Turkey"

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_id_when_no_api_key(self):
        with patch("services.uon_service.UON_API_KEY", ""):
            result = await UonService.get_user_destination("abc")
            assert result is None

    @pytest.mark.asyncio
    async def test_normalizes_country_from_api(self):
        """Страна из API "Турция" должна вернуться как "Turkey"."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "user": [{"country": "Турция", "requests": []}]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        with patch("services.uon_service.UON_API_KEY", "TEST_KEY"), \
             patch.object(UonService, "get_session", return_value=mock_session):
            result = await UonService.get_user_destination("42")
            assert result == "Turkey"

    @pytest.mark.asyncio
    async def test_returns_none_when_api_returns_unknown_country(self):
        """Если API вернул неизвестную страну (200 OK) — must return None."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "user": [{"country": "НенастоящаяСтрана", "requests": []}]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        with patch("services.uon_service.UON_API_KEY", "TEST_KEY"), \
             patch.object(UonService, "get_session", return_value=mock_session):
            result = await UonService.get_user_destination("42")
            assert result is None

    @pytest.mark.asyncio
    async def test_raises_uon_api_error_on_500(self):
        """Если API вернул 500, кидаем UonApiError."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        with patch("services.uon_service.UON_API_KEY", "TEST_KEY"), \
             patch.object(UonService, "get_session", return_value=mock_session):
            with pytest.raises(UonApiError, match="временно недоступен"):
                await UonService.get_user_destination("42")

    @pytest.mark.asyncio
    async def test_raises_uon_api_error_on_network_failure(self):
        """Если сетевая ошибка (ClientError), бросаем UonApiError."""
        mock_session = MagicMock()
        # При попытке войти в контекстный менеджер кидаем ClientError
        mock_session.get.side_effect = ClientError()

        with patch("services.uon_service.UON_API_KEY", "TEST_KEY"), \
             patch.object(UonService, "get_session", return_value=mock_session):
            with pytest.raises(UonApiError, match="Сетевая ошибка"):
                await UonService.get_user_destination("42")
