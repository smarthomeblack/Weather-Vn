"""Sensor platform for Weather Vn integration."""
from __future__ import annotations
from dataclasses import dataclass
import logging
import datetime
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import (
    ATTRIBUTION,
    CONF_PROVINCE,
    CONF_DISTRICT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .data_service import WeatherVnDataService

_LOGGER = logging.getLogger(__name__)


def get_device_info(province: str, district: str) -> DeviceInfo:
    """Trả về device_info cho Weather Vn."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{province}_{district}")},
        name=f"Thời tiết {district.capitalize()}",
        manufacturer="Smarthome Black",
        model="Weather Vn",
        sw_version="2025.7.26",
    )


@dataclass
class WeatherVnSensorEntityDescription(SensorEntityDescription):
    """Class describing Weather Vn sensor entities."""

    unit_fn = None


SENSOR_TYPES: tuple[WeatherVnSensorEntityDescription, ...] = (
    WeatherVnSensorEntityDescription(
        key="aqi",
        name="Chất lượng không khí",
        entity_category=None,
        icon="mdi:air-filter",
    ),
    WeatherVnSensorEntityDescription(
        key="uv",
        name="Chỉ số UV",
        native_unit_of_measurement="UV",
        state_class="measurement",
        device_class=None,
        entity_category=None,
        icon="mdi:weather-sunny-alert",
    ),
    WeatherVnSensorEntityDescription(
        key="apparent_temperature",
        name="Nhiệt độ cảm giác",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class="measurement",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=None,
        icon="mdi:thermometer",
    ),
    WeatherVnSensorEntityDescription(
        key="sunrise",
        name="Mặt trời mọc",
        device_class=None,
        entity_category=None,
        icon="mdi:weather-sunset-up",
    ),
    WeatherVnSensorEntityDescription(
        key="sunset",
        name="Mặt trời lặn",
        device_class=None,
        entity_category=None,
        icon="mdi:weather-sunset-down",
    ),
    WeatherVnSensorEntityDescription(
        key="co",
        name="CO",
        native_unit_of_measurement="ppm",
        device_class=SensorDeviceClass.CO,
        entity_category=None,
        icon="mdi:molecule-co",
    ),
    WeatherVnSensorEntityDescription(
        key="nh3",
        name="NH3",
        native_unit_of_measurement="µg/m³",
        entity_category=None,
        icon="mdi:chemical-weapon",
    ),
    WeatherVnSensorEntityDescription(
        key="no",
        name="NO",
        native_unit_of_measurement="µg/m³",
        entity_category=None,
        icon="mdi:molecule",
    ),
    WeatherVnSensorEntityDescription(
        key="no2",
        name="NO2",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.NITROGEN_DIOXIDE,
        entity_category=None,
        icon="mdi:molecule",
    ),
    WeatherVnSensorEntityDescription(
        key="o3",
        name="O3",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.OZONE,
        entity_category=None,
        icon="mdi:molecule",
    ),
    WeatherVnSensorEntityDescription(
        key="pm2_5",
        name="PM2.5",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.PM25,
        entity_category=None,
        icon="mdi:molecule",
    ),
    WeatherVnSensorEntityDescription(
        key="pm10",
        name="PM10",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.PM10,
        entity_category=None,
        icon="mdi:molecule",
    ),
    WeatherVnSensorEntityDescription(
        key="so2",
        name="SO2",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.SULPHUR_DIOXIDE,
        entity_category=None,
        icon="mdi:molecule",
    ),
    WeatherVnSensorEntityDescription(
        key="temp_low",
        name="Nhiệt độ thấp nhất",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class="measurement",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=None,
        icon="mdi:thermometer-low",
    ),
    WeatherVnSensorEntityDescription(
        key="temp_high",
        name="Nhiệt độ cao nhất",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class="measurement",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=None,
        icon="mdi:thermometer-high",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Weather Vn sensor entries."""
    province = entry.data.get(CONF_PROVINCE)
    district = entry.data.get(CONF_DISTRICT)

    coordinator = AirQualityDataUpdateCoordinator(hass, province, district, entry)
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Thêm các cảm biến tiêu chuẩn
    for description in SENSOR_TYPES:
        entities.append(WeatherVnSensor(coordinator, description, province, district, entry.entry_id))

    # Thêm các cảm biến dự báo theo ngày
    forecast_entities = []
    if coordinator.data and "daily_forecast" in coordinator.data:
        daily_forecast = coordinator.data.get("daily_forecast", [])

        # Tạo các cảm biến cho tối đa 7 ngày dự báo
        for day_index, forecast in enumerate(daily_forecast[:7]):
            day_info = forecast.get("day", "") + " " + forecast.get("date", "")
            if day_info.strip():
                # Nhiệt độ cao
                forecast_entities.append(
                    WeatherVnForecastSensor(
                        coordinator,
                        f"du_bao_ngay_{day_index+1}_temp_high",
                        f"{day_info} - Nhiệt độ cao",
                        "temp_high",
                        day_index,
                        UnitOfTemperature.CELSIUS,
                        SensorDeviceClass.TEMPERATURE,
                        province,
                        district,
                        entry.entry_id,
                        icon="mdi:thermometer-high"
                    )
                )

                # Nhiệt độ thấp
                forecast_entities.append(
                    WeatherVnForecastSensor(
                        coordinator,
                        f"du_bao_ngay_{day_index+1}_temp_low",
                        f"{day_info} - Nhiệt độ thấp",
                        "temp_low",
                        day_index,
                        UnitOfTemperature.CELSIUS,
                        SensorDeviceClass.TEMPERATURE,
                        province,
                        district,
                        entry.entry_id,
                        icon="mdi:thermometer-low"
                    )
                )

                # Điều kiện thời tiết
                forecast_entities.append(
                    WeatherVnForecastSensor(
                        coordinator,
                        f"du_bao_ngay_{day_index+1}_condition",
                        f"{day_info} - Thời tiết",
                        "condition",
                        day_index,
                        None,
                        None,
                        province,
                        district,
                        entry.entry_id,
                        icon="mdi:weather-partly-cloudy"
                    )
                )

                # Độ ẩm
                if "humidity" in forecast:
                    forecast_entities.append(
                        WeatherVnForecastSensor(
                            coordinator,
                            f"du_bao_ngay_{day_index+1}_humidity",
                            f"{day_info} - Độ ẩm",
                            "humidity",
                            day_index,
                            "%",
                            SensorDeviceClass.HUMIDITY,
                            province,
                            district,
                            entry.entry_id,
                            icon="mdi:water-percent"
                        )
                    )

                # Tốc độ gió
                if "wind_speed" in forecast:
                    forecast_entities.append(
                        WeatherVnForecastSensor(
                            coordinator,
                            f"du_bao_ngay_{day_index+1}_wind_speed",
                            f"{day_info} - Gió",
                            "wind_speed",
                            day_index,
                            "m/s",
                            None,
                            province,
                            district,
                            entry.entry_id,
                            icon="mdi:weather-windy"
                        )
                    )

                # Lượng mưa
                if "precipitation" in forecast:
                    forecast_entities.append(
                        WeatherVnForecastSensor(
                            coordinator,
                            f"du_bao_ngay_{day_index+1}_precipitation",
                            f"{day_info} - Lượng mưa",
                            "precipitation",
                            day_index,
                            "mm",
                            None,
                            province,
                            district,
                            entry.entry_id,
                            icon="mdi:weather-rainy"
                        )
                    )

    # Đăng ký entities
    entities.extend(forecast_entities)

    # Thêm entities mới
    async_add_entities(entities, False)


class WeatherVnSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a Weather Vn Sensor."""

    entity_description: WeatherVnSensorEntityDescription
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: AirQualityDataUpdateCoordinator,
        description: WeatherVnSensorEntityDescription,
        province: str,
        district: str,
        entry_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"weathervn-{province}-{district}-{description.key}"
        self._attr_device_info = get_device_info(province, district)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        key = self.entity_description.key

        # Xử lý các loại cảm biến khác nhau
        if key == "aqi":
            return self.coordinator.data.get("air_quality", {}).get("title")
        elif key == "apparent_temperature":
            return self.coordinator.data.get("current_weather", {}).get("apparent_temperature")
        elif key == "uv":
            return self.coordinator.data.get("current_weather", {}).get("uv")
        elif key == "sunrise":
            return self.coordinator.data.get("current_weather", {}).get("sunrise")
        elif key == "sunset":
            return self.coordinator.data.get("current_weather", {}).get("sunset")
        elif key == "temp_low":
            return self.coordinator.data.get("current_weather", {}).get("temp_low")
        elif key == "temp_high":
            return self.coordinator.data.get("current_weather", {}).get("temp_high")
        elif key == "co":
            co_value = self.coordinator.data.get("air_quality", {}).get("co")
            if co_value is not None:
                if hasattr(self.coordinator.data_service, "_convert_ug_to_ppm_for_co"):
                    return self.coordinator.data_service._convert_ug_to_ppm_for_co(co_value)
                return co_value
            return None
        else:
            return self.coordinator.data.get("air_quality", {}).get(key)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {}
        key = self.entity_description.key

        if key == "aqi":
            air_quality = self.coordinator.data.get("air_quality", {})
            aqi_level = air_quality.get("level")
            if aqi_level:
                attributes["level"] = aqi_level
                attributes["description"] = air_quality.get("description", "")

        return attributes


class WeatherVnForecastSensor(CoordinatorEntity, SensorEntity):
    """Cảm biến dự báo theo ngày của Weather Vn."""

    # Bỏ thuộc tính _attr_has_entity_name
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: AirQualityDataUpdateCoordinator,
        key: str,
        name: str,
        forecast_key: str,
        day_index: int,
        unit_of_measurement: str,
        device_class: str,
        province: str,
        district: str,
        entry_id: str,
        icon: str = None,
    ):
        """Khởi tạo cảm biến dự báo."""
        super().__init__(coordinator)
        self._key = key
        self._forecast_key = forecast_key
        self._day_index = day_index

        # Đặt tên đầy đủ cho entity
        self._attr_name = f"{name}"
        self._attr_unique_id = f"weathervn-{province}-{district}-{key}"
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # Đặt là cảm biến thông tin
        self._attr_suggested_object_id = key

        # Đảm bảo ID là đúng định dạng mong muốn
        self.entity_id = f"sensor.{key}"
        self._attr_device_info = get_device_info(province, district)

    @property
    def native_value(self):
        """Trả về giá trị của cảm biến."""
        if not self.coordinator.data or "daily_forecast" not in self.coordinator.data:
            return None

        daily_forecasts = self.coordinator.data.get("daily_forecast", [])

        if len(daily_forecasts) <= self._day_index:
            return None

        forecast = daily_forecasts[self._day_index]
        return forecast.get(self._forecast_key)

    @property
    def extra_state_attributes(self):
        """Trả về các thuộc tính bổ sung của cảm biến."""
        if not self.coordinator.data or "daily_forecast" not in self.coordinator.data:
            return {}

        daily_forecasts = self.coordinator.data.get("daily_forecast", [])

        if len(daily_forecasts) <= self._day_index:
            return {}

        forecast = daily_forecasts[self._day_index]
        attributes = {}

        # Thêm thông tin ngày và thứ
        if "day" in forecast:
            attributes["day"] = forecast["day"]
        if "date" in forecast:
            attributes["date"] = forecast["date"]

        # Thêm các thông tin dự báo khác
        for key, value in forecast.items():
            if key != self._forecast_key and key not in ["day", "date"]:
                attributes[key] = value
        return attributes


class AirQualityDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Weather Vn air quality data."""

    def __init__(self, hass, province, district, config_entry):
        """Initialize."""
        scan_interval = DEFAULT_SCAN_INTERVAL
        if config_entry.options and CONF_SCAN_INTERVAL in config_entry.options:
            scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL)
            _LOGGER.info(f"Sử dụng thời gian cập nhật từ options: {scan_interval} phút")
        elif CONF_SCAN_INTERVAL in config_entry.data:
            scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL)
            _LOGGER.info(f"Sử dụng thời gian cập nhật từ data: {scan_interval} phút")
        else:
            _LOGGER.info(f"Sử dụng thời gian cập nhật mặc định: {scan_interval} phút")

        self.data_service = WeatherVnDataService(province, district, scan_interval)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{province}-{district}-coordinator",
            update_interval=datetime.timedelta(minutes=scan_interval),
            config_entry=config_entry,
        )

    async def _async_update_data(self):
        """Update data via HTTP request."""
        try:
            return await self.data_service.get_data()
        except Exception as err:
            _LOGGER.error("Error while updating air quality data: %s", err)
            return None
