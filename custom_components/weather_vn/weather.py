"""Weather platform for Weather Vn integration."""
from datetime import timedelta, datetime
import logging
from typing import List, Optional
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
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import (
    ATTRIBUTION,
    CONF_PROVINCE,
    CONF_DISTRICT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DISTRICTS,
    CONDITION_CLASSES,
)
from .data_service import WeatherVnDataService
from .sensor import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Weather Vn weather based on config_entry."""
    province = entry.data.get(CONF_PROVINCE)
    district = entry.data.get(CONF_DISTRICT)
    scan_interval = DEFAULT_SCAN_INTERVAL
    if entry.options and CONF_SCAN_INTERVAL in entry.options:
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL)
        _LOGGER.DEBUG(f"Weather: Thời gian cập nhật từ options: {scan_interval} phút")
    elif CONF_SCAN_INTERVAL in entry.data:
        scan_interval = entry.data.get(CONF_SCAN_INTERVAL)
        _LOGGER.DEBUG(f"Weather: Thời gian cập nhật từ data: {scan_interval} phút")
    else:
        _LOGGER.DEBUG(f"Weather: Thời gian cập nhật mặc định: {scan_interval} phút")

    weather = WeatherVnWeather(province, district, entry.entry_id)
    weather._data_service = WeatherVnDataService(province, district, scan_interval)
    weather._data_service.cache_duration = timedelta(minutes=1)
    async_add_entities([weather], True)


class WeatherVnWeather(WeatherEntity):
    """Implementation of Weather Vn weather."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_attribution = ATTRIBUTION

    def __init__(self, province: str, district: str, entry_id: str) -> None:
        """Initialize Weather Vn weather."""
        self._province = province
        self._district = district
        self._entry_id = entry_id
        self._attr_name = f"{DISTRICTS.get(district, district.capitalize())}"
        self._attr_unique_id = f"weathervn-{province}-{district}"
        self._attr_device_info = get_device_info(province, district)
        self._data_service = WeatherVnDataService(province, district, DEFAULT_SCAN_INTERVAL)
        self._forecast_daily = None
        self._forecast_hourly = None

    async def async_update(self) -> None:
        """Update current conditions."""
        try:
            # Luôn lấy dữ liệu mới, không sử dụng cache
            _LOGGER.DEBUG("Weather: Đang cập nhật dữ liệu thời tiết mới...")
            self._data_service.cache_data = None
            self._data_service.cache_time = None
            data = await self._data_service.get_data()
            _LOGGER.DEBUG("Weather: Đã cập nhật dữ liệu thời tiết thành công")
            if not data:
                return

            weather_data = data.get("current_weather", {})
            if weather_data:
                self._attr_native_temperature = weather_data.get("temperature")

                condition_text = weather_data.get("condition", "").lower()
                self._attr_condition = CONDITION_CLASSES.get(condition_text, "exceptional")

                if "humidity" in weather_data:
                    self._attr_humidity = weather_data.get("humidity")

                if "wind_speed" in weather_data:
                    self._attr_native_wind_speed = weather_data.get("wind_speed")

                if "dew_point" in weather_data:
                    self._attr_native_dew_point = weather_data.get("dew_point")

            self._forecast_daily = data.get("daily_forecast", [])
            self._forecast_hourly = data.get("hourly_forecast", [])

        except Exception as e:
            _LOGGER.error(f"Error updating Weather Vn data: {e}")

    @property
    def forecast(self) -> Optional[List[Forecast]]:
        """Return the forecast."""
        return self.forecast_daily

    @property
    def forecast_daily(self) -> Optional[List[Forecast]]:
        """Return daily forecast."""
        if not self._forecast_daily:
            return None

        ha_forecasts = []
        for forecast in self._forecast_daily:
            condition_text = forecast.get("condition", "").lower()
            condition = CONDITION_CLASSES.get(condition_text, "exceptional")

            forecast_item = {
                "condition": condition,
                "native_temperature": forecast.get("temp_high"),
                "native_templow": forecast.get("temp_low"),
            }

            # Thêm date nếu có - chuyển đổi từ chuỗi "DD/MM" sang đối tượng datetime ISO format
            date_text = forecast.get("date", "")
            if date_text:
                try:
                    day, month = map(int, date_text.split("/"))
                    year = datetime.now().year
                    if month == 1 and datetime.now().month == 12:
                        year += 1
                    date_obj = datetime(year, month, day).isoformat()
                    forecast_item["datetime"] = date_obj
                except (ValueError, IndexError):
                    forecast_item["datetime"] = date_text

            ha_forecasts.append(forecast_item)

        return ha_forecasts

    async def async_forecast_daily(self) -> Optional[List[Forecast]]:
        """Return daily forecast."""
        return self.forecast_daily

    @property
    def forecast_hourly(self) -> Optional[List[Forecast]]:
        """Return hourly forecast."""
        if not self._forecast_hourly:
            return None

        ha_forecasts = []
        for forecast in self._forecast_hourly:
            condition_text = forecast.get("condition", "").lower()
            condition = CONDITION_CLASSES.get(condition_text, "exceptional")

            forecast_item = {
                "condition": condition,
                "native_temperature": forecast.get("temp"),
                "humidity": forecast.get("humidity"),
            }

            # Thêm time nếu có - chuyển đổi sang định dạng ISO
            time_text = forecast.get("time", "")
            if time_text:
                try:
                    hour_str, minute_str = time_text.split(":")
                    hour = int(hour_str)
                    minute = int(minute_str.split()[0])
                    is_pm = "pm" in time_text.lower()

                    if is_pm and hour < 12:
                        hour += 12
                    elif not is_pm and hour == 12:
                        hour = 0

                    now = datetime.now()
                    forecast_datetime = now.replace(hour=hour, minute=minute)

                    if forecast_datetime < now:
                        forecast_datetime = forecast_datetime + timedelta(days=1)

                    forecast_item["datetime"] = forecast_datetime.isoformat()
                except (ValueError, IndexError):
                    forecast_item["datetime"] = time_text

            ha_forecasts.append(forecast_item)

        return ha_forecasts

    async def async_forecast_hourly(self) -> Optional[List[Forecast]]:
        """Return hourly forecast."""
        return self.forecast_hourly
