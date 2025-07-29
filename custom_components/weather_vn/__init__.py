"""Weather Vn integration."""
import logging
import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_PROVINCE,
    CONF_DISTRICT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from .data_service import WeatherVnDataService, WeatherVnDataError

_LOGGER = logging.getLogger(__name__)


PLATFORMS = [Platform.WEATHER, Platform.SENSOR]


class WeatherVnDataUpdateCoordinator(DataUpdateCoordinator):
    """Lớp quản lý việc lấy dữ liệu Weather VN."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Khởi tạo."""
        self.province = entry.data.get(CONF_PROVINCE)
        self.district = entry.data.get(CONF_DISTRICT)
        self.data_service = WeatherVnDataService(self.province, self.district)

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.province}-{self.district}",
            update_interval=datetime.timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self):
        """Cập nhật dữ liệu qua API."""
        try:
            return await self.data_service.get_data()
        except WeatherVnDataError as err:
            raise UpdateFailed(f"Lỗi khi lấy dữ liệu: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Thiết lập Weather Vn từ mục cấu hình."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = WeatherVnDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Gỡ bỏ mục cấu hình."""
    # Xóa coordinator khỏi hass.data
    hass.data[DOMAIN].pop(entry.entry_id)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
