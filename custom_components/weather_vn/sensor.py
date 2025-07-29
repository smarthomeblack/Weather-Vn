"""Nền tảng cảm biến tích hợp Weather Vn."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import logging
import datetime
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfLength,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import (
    ATTRIBUTION,
    CONF_PROVINCE,
    CONF_DISTRICT,
    DOMAIN,
)
from . import WeatherVnDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def get_device_info(province: str, district: str) -> DeviceInfo:
    """Trả về device_info cho Weather Vn."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{province}_{district}")},
        name=f"Thời tiết {district.capitalize()}",
        manufacturer="Smarthome Black",
        model="Weather Vn",
        sw_version="2025.7.28",
    )


@dataclass
class WeatherVnSensorEntityDescription(SensorEntityDescription):
    """Lớp mô tả các thực thể cảm biến Weather Vn."""

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
        key="pressure",
        name="Áp suất",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.PRESSURE,
        entity_category=None,
        icon="mdi:gauge",
    ),
    WeatherVnSensorEntityDescription(
        key="visibility",
        name="Tầm nhìn",
        native_unit_of_measurement="km",
        entity_category=None,
        icon="mdi:eye",
    ),
    WeatherVnSensorEntityDescription(
        key="wind_gust",
        name="Gió giật",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        entity_category=None,
        icon="mdi:weather-windy-variant",
    ),
    WeatherVnSensorEntityDescription(
        key="precipitation_amount",
        name="Lượng mưa",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        entity_category=None,
        icon="mdi:weather-pouring",
    ),
    WeatherVnSensorEntityDescription(
        key="precipitation_accumulation",
        name="Lượng mưa tích tụ",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        entity_category=None,
        icon="mdi:weather-rainy",
    ),
    WeatherVnSensorEntityDescription(
        key="precipitation_probability",
        name="Khả năng mưa giờ sau",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=None,
        icon="mdi:weather-rainy",
    ),
    WeatherVnSensorEntityDescription(
        key="precipitation_next_hour_amount",
        name="Lượng mưa giờ sau",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        icon="mdi:weather-pouring",
    ),
    WeatherVnSensorEntityDescription(
        key="precipitation_next_hour_accumulation",
        name="Tích tụ giờ sau",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        icon="mdi:weather-rainy",
    ),
    WeatherVnSensorEntityDescription(
        key="precipitation_today",
        name="Lượng mưa hôm nay",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        icon="mdi:calendar-today",
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
    """Thiết lập mục nhập cảm biến Weather Vn."""
    province = entry.data.get(CONF_PROVINCE)
    district = entry.data.get(CONF_DISTRICT)
    entry_id = entry.entry_id

    coordinator: WeatherVnDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Thêm các cảm biến tiêu chuẩn
    for description in SENSOR_TYPES:
        entities.append(WeatherVnSensor(coordinator, description, province, district, entry.entry_id))

    # ---- KHÔI PHỤC LOGIC TẠO CẢM BIẾN DỰ BÁO ----
    forecast_entities = []
    if coordinator.data and "daily_forecast" in coordinator.data:
        daily_forecast = coordinator.data.get("daily_forecast", [])

        # Tạo các cảm biến cho tối đa 7 ngày dự báo
        for day_index, forecast in enumerate(daily_forecast[:7]):
            try:
                # Lấy ngày từ 'datetime' và định dạng lại
                forecast_date_str = forecast.get("datetime", "")
                if not forecast_date_str:
                    continue

                forecast_date = datetime.datetime.fromisoformat(forecast_date_str.split('T')[0])
                day_info = f"Ngày {forecast_date.strftime('%d/%m')}"

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
                            UnitOfSpeed.METERS_PER_SECOND,  # Dữ liệu đã là m/s
                            SensorDeviceClass.WIND_SPEED,
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
                            UnitOfLength.MILLIMETERS,
                            SensorDeviceClass.PRECIPITATION,
                            province,
                            district,
                            entry.entry_id,
                            icon="mdi:weather-rainy"
                        )
                    )
                # Khả năng có mưa
                if "precipitation_probability" in forecast:
                    forecast_entities.append(
                        WeatherVnForecastSensor(
                            coordinator,
                            f"du_bao_ngay_{day_index+1}_precipitation_probability",
                            f"{day_info} - Khả năng có mưa",
                            "precipitation_probability",
                            day_index,
                            PERCENTAGE,
                            None,
                            province,
                            district,
                            entry.entry_id,
                            icon="mdi:weather-rainy"
                        )
                    )
            except Exception as e:
                _LOGGER.debug(f"Lỗi khi tạo cảm biến dự báo cho ngày {day_index}: {e}")
                continue

    # Đăng ký entities
    entities.extend(forecast_entities)

    # Thêm entities mới
    async_add_entities(entities, False)

    # ---- THÊM LOGIC TẠO CẢM BIẾN HOẠT ĐỘNG ----
    life_entities = []
    if coordinator.data and "activities" in coordinator.data:
        activities = coordinator.data.get("activities", [])
        for activity in activities:
            try:
                life_entities.append(
                    WeatherVnLifeSensor(
                        coordinator,
                        activity,
                        province,
                        district,
                        entry_id
                    )
                )
            except Exception as e:
                _LOGGER.debug(f"Lỗi khi tạo cảm biến hoạt động {activity.get('name')}: {e}")

    if life_entities:
        async_add_entities(life_entities, False)


class WeatherVnSensor(CoordinatorEntity, SensorEntity):
    """Triển khai cảm biến thời tiết."""

    entity_description: WeatherVnSensorEntityDescription
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: WeatherVnDataUpdateCoordinator,
        description: WeatherVnSensorEntityDescription,
        province: str,
        district: str,
        entry_id: str,
    ):
        """Khởi tạo cảm biến."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"weathervn-{province}-{district}-{description.key}"
        self._attr_device_info = get_device_info(province, district)

    @property
    def available(self) -> bool:
        """Trả về True nếu thực thể có sẵn."""
        return self.coordinator.data is not None

    @property
    def native_value(self):
        """Trả về trạng thái của cảm biến."""
        if not self.coordinator.data:
            return None

        key = self.entity_description.key
        current_weather = self.coordinator.data.get("current_weather", {})
        air_quality = self.coordinator.data.get("air_quality", {})

        # Xử lý các loại cảm biến khác nhau
        if key == "aqi":
            return air_quality.get("title")
        elif key in [
            "apparent_temperature", "uv", "sunrise", "sunset",
            "pressure", "visibility", "wind_gust", "precipitation_amount",
            "precipitation_accumulation", "precipitation_probability",
            "precipitation_next_hour_amount", "precipitation_next_hour_accumulation",
            "precipitation_today", "temp_low", "temp_high"
        ]:
            return current_weather.get(key)
        elif key == "co":
            co_value = air_quality.get("co")
            if co_value is not None:
                if hasattr(self.coordinator.data_service, "_convert_ug_to_ppm_for_co"):
                    return self.coordinator.data_service._convert_ug_to_ppm_for_co(co_value)
                return co_value
            return None
        else:
            return air_quality.get(key)

    @property
    def extra_state_attributes(self):
        """Trả về các thuộc tính trạng thái."""
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


# ---- THÊM LỚP WeatherVnLifeSensor MỚI ----
class WeatherVnLifeSensor(CoordinatorEntity, SensorEntity):
    """Cảm biến hoạt động đời sống của Weather VN."""

    def __init__(
        self,
        coordinator: WeatherVnDataUpdateCoordinator,
        activity_data: dict,
        province: str,
        district: str,
        entry_id: str
    ):
        """Khởi tạo cảm biến."""
        super().__init__(coordinator)
        self._activity_data = activity_data
        self._attr_name = activity_data.get("name", "Không xác định")
        # Gộp chuỗi unique_id cho ngắn, tránh quá dài dòng
        self._attr_unique_id = (
            f"weathervn-{province}-{district}-life_"
            f"{activity_data.get('type')}_{activity_data.get('subType')}"
        )
        self._attr_device_info = get_device_info(province, district)
        self._attr_icon = self._get_icon_for_activity(activity_data.get("type"))
        # entity_id không nên quá dài, loại bỏ ký tự đặc biệt và viết thường
        ten = self._attr_name.lower().replace(" ", "_")
        self.entity_id = f"sensor.{DOMAIN}_{province}_{district}_life_{ten}"

    @property
    def native_value(self) -> str | None:
        """Trạng thái của cảm biến (lấy từ taskbarSummary)."""
        # Dữ liệu được cập nhật tự động bởi CoordinatorEntity
        for activity in self.coordinator.data.get("activities", []):
            if (activity.get("type") == self._activity_data.get("type") and
                    activity.get("subType") == self._activity_data.get("subType")):
                return activity.get("state")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Thuộc tính của cảm biến (lấy từ summary)."""
        for activity in self.coordinator.data.get("activities", []):
            if (activity.get("type") == self._activity_data.get("type") and
                    activity.get("subType") == self._activity_data.get("subType")):
                return {"summary": activity.get("summary")}
        return None

    @property
    def available(self) -> bool:
        """Trả về True nếu thực thể có sẵn."""
        return super().available and self.coordinator.data is not None and any(
            activity.get("type") == self._activity_data.get("type") and
            activity.get("subType") == self._activity_data.get("subType")
            for activity in self.coordinator.data.get("activities", [])
        )

    def _get_icon_for_activity(self, activity_type: int) -> str:
        """Lấy icon dựa trên loại hoạt động."""
        if activity_type == 1:  # Sức khỏe & An toàn
            return "mdi:heart-pulse"
        if activity_type == 2:  # Điều kiện
            return "mdi:car-cog"
        if activity_type == 3:  # Hoạt động ngoài trời
            return "mdi:walk"
        return "mdi:help-rhombus-outline"


class WeatherVnForecastSensor(CoordinatorEntity, SensorEntity):
    """Đại diện cho một cảm biến dự báo Weather Vn."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeatherVnDataUpdateCoordinator,
        key: str,
        name: str,
        forecast_key: str,
        day_index: int,
        unit_of_measurement: str | None,
        device_class: SensorDeviceClass | None,
        province: str,
        district: str,
        entry_id: str,
        icon: str | None = None,
    ):
        """Khởi tạo cảm biến dự báo."""
        super().__init__(coordinator)
        self._key = key
        self._forecast_key = forecast_key
        self._day_index = day_index

        self._attr_name = name
        self._attr_unique_id = f"weathervn-{province}-{district}-{key}"
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self.entity_id = f"sensor.{DOMAIN}_{province}_{district}_{key}"
        self._attr_device_info = get_device_info(province, district)

    @property
    def available(self) -> bool:
        """Trả về True nếu thực thể có sẵn."""
        return self.coordinator.data is not None

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

        # Thêm các thông tin dự báo khác làm thuộc tính
        for key, value in forecast.items():
            if key != self._forecast_key:
                attributes[key] = value
        return attributes
