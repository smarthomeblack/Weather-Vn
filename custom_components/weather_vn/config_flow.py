"""Luồng cấu hình để tích hợp Weather Vn."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from .const import (
    DOMAIN,
    PROVINCES,
    DISTRICTS,
    CONF_PROVINCE,
    CONF_DISTRICT,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    _load_json_data_async,
)

_LOGGER = logging.getLogger(__name__)


class WeatherVnConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Xử lý luồng cấu hình cho Weather Vn."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Tạo luồng tùy chọn."""
        return WeatherVnOptionsFlow(config_entry)

    def __init__(self):
        """Khởi tạo luồng cấu hình."""
        self._province = None
        self._districts = {}
        self._scan_interval = DEFAULT_SCAN_INTERVAL

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Xử lý bước đầu tiên để chọn tỉnh."""
        errors = {}

        if user_input is not None:
            self._province = user_input[CONF_PROVINCE]
            self._scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            return await self.async_step_district()

        provinces_list = {k: v for k, v in PROVINCES.items()}

        schema = vol.Schema(
            {
                vol.Required(CONF_PROVINCE): vol.In(provinces_list),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self._scan_interval,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=180,
                        step=5,
                        mode=selector.NumberSelectorMode.SLIDER,
                        unit_of_measurement="phút",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_district(self, user_input=None) -> FlowResult:
        """Xử lý bước chọn quận."""
        errors = {}

        if user_input is not None:
            province = self._province
            district = user_input[CONF_DISTRICT]

            # Kiểm tra xem đã cấu hình tỉnh/huyện này chưa
            await self.async_set_unique_id(f"{province}-{district}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{PROVINCES.get(province, province)} - {DISTRICTS.get(district, district)}",
                data={
                    CONF_PROVINCE: province,
                    CONF_DISTRICT: district,
                    CONF_SCAN_INTERVAL: self._scan_interval,
                },
            )

        # Lấy danh sách quận/huyện từ file JSON - sử dụng phiên bản async
        provinces_data = await _load_json_data_async(self.hass, "provinces_districts.json")
        province_data = provinces_data.get(self._province, {})
        districts_dict = province_data.get("districts", {})

        if not districts_dict:
            # Nếu không có quận/huyện nào cho tỉnh này thì quay lại bước chọn tỉnh
            return await self.async_step_user()

        districts_list = {}
        for district_id, district_name in districts_dict.items():
            districts_list[district_id] = district_name

        return self.async_show_form(
            step_id="district",
            data_schema=vol.Schema(
                {vol.Required(CONF_DISTRICT): vol.In(districts_list)}
            ),
            errors=errors,
        )


class WeatherVnOptionsFlow(config_entries.OptionsFlow):
    """Xử lý luồng tùy chọn cho tích hợp Weather Vn."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Khởi tạo luồng tùy chọn."""
        self._entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Quản lý tùy chọn."""
        errors = {}
        current_scan_interval = self._entry.options.get(
            CONF_SCAN_INTERVAL,
            self._entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        if user_input is not None:
            try:
                scan_interval = int(user_input[CONF_SCAN_INTERVAL])
                if 5 <= scan_interval <= 180:
                    # Chỉ lưu thời gian cập nhật vào options
                    options = {
                        CONF_SCAN_INTERVAL: scan_interval,
                    }
                    return self.async_create_entry(title="", data=options)
                else:
                    errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
            except (ValueError, KeyError) as ex:
                _LOGGER.error(f"Lỗi xử lý tùy chọn: {ex}")
                errors["base"] = "unknown"

        # Hiển thị form
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=180,
                        step=5,
                        mode=selector.NumberSelectorMode.SLIDER,
                        unit_of_measurement="phút",
                    )
                ),
            }),
            errors=errors,
            description_placeholders={
                "current_interval": f"{current_scan_interval}"
            }
        )
