import json
from unittest.mock import patch, mock_open, MagicMock
from custom_components.global_earthquakes.cache import GlobalEarthquakeCache


def test_cache_management():
    hass = MagicMock()
    cache = GlobalEarthquakeCache(hass, "Test Instance")

    assert "test_instance" in cache.cache_path

    # 1. Load missing cache
    with patch("os.path.exists", return_value=False):
        assert cache.load_cache() == []

    # 2. Load valid cache
    mock_data = [{"id": "eq1"}]
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(mock_data))),
    ):
        assert cache.load_cache() == mock_data

    # 3. Load corrupted cache
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data="NOT JSON FORMAT")),
    ):
        assert cache.load_cache() == []

    # 4. Save cache
    with patch("builtins.open", mock_open()) as m_open:
        cache.save_cache(mock_data)
        m_open.assert_called_once_with(cache.cache_path, "w", encoding="utf-8")

    # 5. Clear cache
    with patch("os.path.exists", return_value=True), patch("os.remove") as m_remove:
        cache.clear_cache()
        m_remove.assert_called_once_with(cache.cache_path)
