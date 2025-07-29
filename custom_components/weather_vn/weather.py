"""Nền tảng thời tiết để tích hợp Weather Vn."""
from __future__ import annotations
import logging
from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONDITION_CLASSES,
    DOMAIN,
)
from . import WeatherVnDataUpdateCoordinator
from .sensor import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Thiết lập thời tiết Weather Vn ."""
    coordinator: WeatherVnDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WeatherVnWeather(coordinator)], True)


class WeatherVnWeather(CoordinatorEntity, WeatherEntity):
    """Triển khai dự báo thời tiết Weather Vn."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: WeatherVnDataUpdateCoordinator) -> None:
        """Khởi tạo thời tiết Weather Vn."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.district.capitalize()}"
        self._attr_unique_id = f"weathervn-{coordinator.province}-{coordinator.district}"
        self._attr_device_info = get_device_info(coordinator.province, coordinator.district)

    @property
    def available(self) -> bool:
        """Trả về true nếu coordinator có dữ liệu."""
        return self.coordinator.data is not None

    @property
    def condition(self) -> str | None:
        """Trả về điều kiện thời tiết hiện tại."""
        if not self.available:
            return None
        condition_text = self.coordinator.data.get("current_weather", {}).get("condition", "").lower()
        return CONDITION_CLASSES.get(condition_text)

    @property
    def native_temperature(self) -> float | None:
        """Trả về nhiệt độ hiện tại."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("temperature")

    @property
    def native_temperature_high(self) -> float | None:
        """Trả về nhiệt độ cao nhất hôm nay."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("temp_high")

    @property
    def native_temperature_low(self) -> float | None:
        """Trả về nhiệt độ thấp nhất hôm nay."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("temp_low")

    @property
    def humidity(self) -> float | None:
        """Trả về độ ẩm."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("humidity")

    @property
    def native_wind_speed(self) -> float | None:
        """Trả về tốc độ gió."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("wind_speed")

    @property
    def native_pressure(self) -> float | None:
        """Trả về áp suất."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("pressure")

    @property
    def native_visibility(self) -> float | None:
        """Trả về tầm nhìn."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("visibility")

    @property
    def native_precipitation_value(self) -> float | None:
        """Trả về lượng mưa hiện tại (lấy từ dự báo 2 giờ)."""
        if not self.available:
            return None
        return self.coordinator.data.get("current_weather", {}).get("precipitation_amount")

    @property
    def forecast_daily(self) -> list[Forecast] | None:
        """Trả về dự báo thời tiết hàng ngày."""
        if not self.available or not self.coordinator.data.get("daily_forecast"):
            return None

        ha_forecasts: list[Forecast] = []
        for forecast in self.coordinator.data["daily_forecast"]:
            condition_text = (forecast.get("condition") or "").lower()
            condition = CONDITION_CLASSES.get(condition_text, "exceptional")

            ha_forecasts.append(
                {
                    "datetime": forecast.get("datetime"),
                    "condition": condition,
                    "native_temperature": forecast.get("temp_high"),
                    "native_templow": forecast.get("temp_low"),
                    "native_precipitation_value": forecast.get("precipitation"),
                    "precipitation_probability": forecast.get("precipitation_probability"),
                    "humidity": forecast.get("humidity"),
                    "native_wind_speed": forecast.get("wind_speed"),
                }
            )
        return ha_forecasts

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Trả về dự báo hàng ngày."""
        return self.forecast_daily

    @property
    def forecast_hourly(self) -> list[Forecast] | None:
        """Trả về dự báo thời tiết hàng giờ."""
        if not self.available or not self.coordinator.data.get("hourly_forecast"):
            return None

        ha_forecasts: list[Forecast] = []
        for forecast in self.coordinator.data["hourly_forecast"]:
            condition_text = (forecast.get("condition") or "").lower()
            condition = CONDITION_CLASSES.get(condition_text, "exceptional")

            ha_forecasts.append(
                {
                    "datetime": forecast.get("datetime"),
                    "condition": condition,
                    "native_temperature": forecast.get("temperature"),
                    "native_apparent_temperature": forecast.get("apparent_temperature"),
                    "humidity": forecast.get("humidity"),
                    "precipitation_probability": forecast.get("precipitation_probability"),
                    "native_wind_speed": forecast.get("wind_speed"),
                    "native_precipitation_value": forecast.get("precipitation"),
                }
            )
        return ha_forecasts

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Trả về dự báo hàng giờ."""
        return self.forecast_hourly
